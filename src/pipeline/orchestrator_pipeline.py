# This file got pretty ai slopped from claude. Whoops.

import asyncio
import logging
from agents import TResponseInputItem, ItemHelpers
from util import RetryRunner
from service_agents import getOrchestratorAgent, getEvaluatorAgent
from service_agents.evaluation_agent import EvaluationFeedback

# Configure logging to include detailed trace information
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.CRITICAL,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

async def orchestrator_pipeline():
    """
    Pipeline that uses orchestrator and evaluator agents to build a project.
    Tracing is added at every step to track what each agent is thinking and responding.
    """

    # Welcome and introductory messages
    logging.info("=" * 60)
    logging.info("🤖 Senior Developer Agent Assistant 🤖".center(60))
    logging.info("=" * 60)
    logging.info("Displayed welcome message and instructions for user.")

    print("\nI'll help you with software development tasks by using a team of specialized agents.")
    print("Let me know what you need help with, and I'll coordinate the right specialists to solve it.\n")

    # Get initial user request
    user_request = input("What software development task can I help you with? ")
    logging.debug(f"User request received: {user_request}")
    input_items: list[TResponseInputItem] = [{"content": user_request, "role": "user"}]

    # Initialize tracking variables
    latest_solution: str | None = None
    evaluation_result: EvaluationFeedback | None = None
    iteration_count = 0
    max_iterations = 5  # Prevent infinite loops

    # Initialize the evaluator and orchestrator agents
    evaluator = getEvaluatorAgent()
    orchestrator = getOrchestratorAgent()
    logging.debug("Evaluator and Orchestrator agents initialized.")

    try:
        logging.info("Starting analysis and context gathering.")
        print("\n📋 Analyzing your request and gathering context...\n")

        # Main solution development loop
        while (not evaluation_result or evaluation_result.score == "needs_improvement") and iteration_count < max_iterations:
            iteration_count += 1
            logging.info(f"Iteration {iteration_count}/{max_iterations} - working on solution.")
            print(f"\n📝 Working on solution (Iteration {iteration_count}/{max_iterations})...")

            # --- Orchestrator Step ---
            try:
                logging.debug("Calling orchestrator agent with current input items.")
                orchestrator_result = await RetryRunner.run(orchestrator, input_items)
                logging.debug("Received result from orchestrator.")

                input_items.append({"content": "Wait... Did you properly use the coding agent and testing agent to implement your solution... and they wrote to the directory?", "role": "user"})

                orchestrator_result = await RetryRunner.run(orchestrator, input_items)

                # Update input for the next step and store latest solution
                input_items = orchestrator_result.to_input_list()
                latest_solution = ItemHelpers.text_message_outputs(orchestrator_result.new_items)
                logging.debug(f"Updated solution from orchestrator: {latest_solution}")

                print(f"\n✨ Current solution progress:\n{'-'*60}\n{latest_solution}\n{'-'*60}")
            except Exception as orchestration_error:
                logging.error(f"Error during orchestration: {orchestration_error}")
                print(f"\n❌ Error during orchestration: {orchestration_error}")
                if iteration_count >= max_iterations // 2:
                    logging.warning("Multiple orchestration errors encountered; proceeding with partial solution.")
                    print("Continuing with partial solution...")
                    if not latest_solution:
                        logging.error("No partial solution available after orchestration error. Exiting.")
                        print("No solution available. Please try again.")
                        return
                else:
                    error_message = f"The previous attempt encountered an error: {orchestration_error}. Please try a different approach."
                    input_items.append({"content": error_message, "role": "developer"})
                    logging.debug("Appended error feedback to input items; will retry.")
                    continue

            # --- Evaluator Step ---
            try:
                logging.debug("Calling evaluator agent to assess current solution.")
                evaluator_result = await RetryRunner.run(evaluator, input_items)
                evaluation_result = evaluator_result.final_output
                logging.debug(f"Evaluator returned: score={evaluation_result.score}, feedback={evaluation_result.feedback}")

                print(f"\n🔍 Evaluation Score: {evaluation_result.score}")
                print(f"📊 Feedback: {evaluation_result.feedback}")

                if evaluation_result.score == "needs_improvement" and iteration_count < max_iterations:
                    feedback_message = f"Please address this feedback: {evaluation_result.feedback}"
                    input_items.append({"content": feedback_message, "role": "user"})
                    logging.info("Evaluator feedback appended for further refinement.")
                    print("\n🔄 Refining solution based on feedback...\n")
            except Exception as evaluation_error:
                logging.error(f"Error during evaluation: {evaluation_error}")
                print(f"\n❌ Error during evaluation: {evaluation_error}")
                if latest_solution:
                    logging.info("Continuing with current solution despite evaluation error.")
                    print("Continuing with current solution...")
                    evaluation_result = EvaluationFeedback(score="pass", feedback="Evaluation failed, but solution is available.")
                else:
                    logging.error("No solution available after evaluation error. Exiting.")
                    print("No solution available. Please try again.")
                    return

        # --- Finalize and Deliver Solution ---
        logging.info("Finalizing solution delivery.")
        print("\n" + "=" * 60)
        if evaluation_result and evaluation_result.score == "pass":
            print("✅ FINAL SOLUTION COMPLETE")
            logging.info("Solution completed successfully.")
        elif iteration_count >= max_iterations:
            print("⚠️ MAXIMUM ITERATIONS REACHED")
            logging.warning("Reached maximum iterations without complete solution.")
        else:
            print("⚠️ SOLUTION NEEDS IMPROVEMENT")
            logging.info("Solution still requires improvement.")

        print("=" * 60 + "\n")
        print(f"{latest_solution}\n")
        logging.debug("Final solution displayed to user.")
            
    except KeyboardInterrupt:
        logging.info("Operation cancelled by user (KeyboardInterrupt).")
        print("\n\nOperation cancelled by user. Exiting...")
    except Exception as general_error:
        logging.exception(f"Unexpected error occurred: {general_error}")
        print(f"\n❌ An unexpected error occurred: {general_error}")
        if latest_solution:
            logging.info("Providing partial solution due to unexpected error.")
            print("\nHere's the partial solution I was able to develop:")
            print(f"\n{latest_solution}\n")