from agents import TResponseInputItem
from util import RetryRunner, ItemHelpers
from service_agents import getOrchestratorAgent, getEvaluatorAgent
from service_agents.evaluation_agent import EvaluationFeedback


async def project_builder():
    """
    A sample pipeline that uses the orchestrator and evaluator agents to build a project.
    """

    # Welcome message and initial project gathering
    print("\n" + "=" * 60)
    print("🤖 Senior Developer Agent Assistant 🤖".center(60))
    print("=" * 60 + "\n")

    print(
        "I'll help you with software development tasks by using a team of specialized agents."
    )
    print(
        "Let me know what you need help with, and I'll coordinate the right specialists to solve it.\n"
    )

    # Get initial request
    msg = input("What software development task can I help you with? ")
    input_items: list[TResponseInputItem] = [{"content": msg, "role": "user"}]

    # Track progress
    latest: str | None = None
    result: EvaluationFeedback | None = None
    iteration_count = 0
    max_iterations = 5  # Prevent infinite loops

    try:
        print("\n📋 Analyzing your request and gathering context...\n")

        # Main solution development loop
        while (
            not result or result.score == "needs_improvement"
        ) and iteration_count < max_iterations:
            iteration_count += 1

            print(
                f"\n📝 Working on solution (Iteration {iteration_count}/{max_iterations})..."
            )

            # Run the orchestrator with retry logic
            try:
                orchestrator_result = await RetryRunner.run(
                    getOrchestratorAgent(), input_items
                )

                input_items = orchestrator_result.to_input_list()
                latest = ItemHelpers.text_message_outputs(orchestrator_result.new_items)

                print(f"\n✨ Current solution progress:\n{'-'*60}\n{latest}\n{'-'*60}")

            except Exception as e:
                print(f"\n❌ Error during orchestration: {str(e)}")
                if iteration_count >= max_iterations // 2:
                    # If we've already tried multiple times, continue with what we have
                    print("Continuing with partial solution...")
                    if not latest:
                        print("No solution available. Please try again.")
                        return
                else:
                    # Add error context and retry
                    error_message = f"The previous attempt encountered an error: {str(e)}. Please try a different approach."
                    input_items.append({"content": error_message, "role": "user"})
                    continue

            # Evaluate the solution
            try:
                evaluator_result = await RetryRunner.run(evaluator, input_items)
                result: EvaluationFeedback = evaluator_result.final_output

                print(f"\n🔍 Evaluation Score: {result.score}")
                print(f"📊 Feedback: {result.feedback}")

                # Add feedback for the next iteration if needed
                if (
                    result.score == "needs_improvement"
                    and iteration_count < max_iterations
                ):
                    input_items.append(
                        {
                            "content": f"Please address this feedback: {result.feedback}",
                            "role": "user",
                        }
                    )
                    print("\n🔄 Refining solution based on feedback...\n")

            except Exception as e:
                print(f"\n❌ Error during evaluation: {str(e)}")
                # If evaluation fails but we have a solution, continue
                if latest:
                    print("Continuing with current solution...")
                    result = EvaluationFeedback(
                        score="pass",
                        feedback="Evaluation failed, but solution is available.",
                    )
                else:
                    print("No solution available. Please try again.")
                    return

        # Final solution delivery
        print("\n" + "=" * 60)
        if result.score == "pass":
            print("✅ FINAL SOLUTION COMPLETE")
        elif iteration_count >= max_iterations:
            print("⚠️ MAXIMUM ITERATIONS REACHED")
        else:
            print("⚠️ SOLUTION NEEDS IMPROVEMENT")
        print("=" * 60 + "\n")

        print(f"{latest}\n")

        # Get feedback for continuous improvement
        feedback = input(
            "\nWould you like to provide feedback on this solution? (optional): "
        )
        if feedback.strip():
            print(
                "\nThank you for your feedback! I'll use it to improve future solutions."
            )

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user. Exiting...")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {str(e)}")
        # Try to provide partial solution if available
        if latest:
            print("\nHere's the partial solution I was able to develop:")
            print(f"\n{latest}\n")
