import asyncio
import logging
from agents import TResponseInputItem, ItemHelpers
from util import RetryRunner
from service_agents import getEvaluatorAgent, getPlanningAgent, getCodingAgent, getTestingAgent, getLLMContextManagementAgent
from service_agents.evaluation_agent import EvaluationFeedback

# Configure logging to include detailed trace information
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

async def managed_pipeline():
    """
    Pipeline that uses discrete steps for each agent.
    """

    # Get initial user request
    user_request = input("What do you want to build?")
    logging.debug(f"User request received: {user_request}")
    input_items: list[TResponseInputItem] = [{"content": user_request, "role": "user"}]

    # Initialize tracking variables
    evaluation_result: EvaluationFeedback | None = None
    iteration_count = 0
    max_iterations = 5  # Prevent infinite loops

    # Initialize the evaluator and orchestrator agents
    planner = getPlanningAgent()
    coder = getCodingAgent()
    tester = getTestingAgent()
    evaluator = getEvaluatorAgent()
    context_management_agent = getLLMContextManagementAgent()
    logging.debug("Evaluator and Orchestrator agents initialized.")

    try:
        logging.info("Starting solution development.")

        # Main solution development loop
        while (not evaluation_result or evaluation_result.score == "needs_improvement") and iteration_count < max_iterations:
            iteration_count += 1
            logging.info(f"Iteration {iteration_count}/{max_iterations} - working on solution.")
            print(f"Iteration {iteration_count}/{max_iterations}")

            # --- Planner Step ---
            planner_result = await RetryRunner.run(planner, input_items)
            input_items.append({"content": planner_result.final_output, "role": "assistant"})
            input_items.append({"content": "Planner completed. Coding agent please start coding.", "role": "user"})
            
            # --- Coding Step ---
            coder_result = await RetryRunner.run(coder, input_items)
            input_items.append({"content": coder_result.final_output, "role": "assistant"})
            input_items.append({"content": "Coding completed. Testing agent please start testing.", "role": "user"})
            
            # --- Testing Step ---
            tester_result = await RetryRunner.run(tester, input_items)
            input_items.append({"content": tester_result.final_output, "role": "assistant"})
            input_items.append({"content": "Testing completed. Evaluator please start evaluating.", "role": "user"})

            # --- Evaluator Step ---
            logging.debug("Calling evaluator agent to assess current solution.")
            evaluator_result = await RetryRunner.run(evaluator, input_items)
            evaluation_result = evaluator_result.final_output
            logging.debug(f"Evaluator returned: score={evaluation_result.score}, feedback={evaluation_result.feedback}")

            if evaluation_result.score == "needs_improvement" and iteration_count < max_iterations:
                input_items.append({"content": "Evaluation completed. Context management agent please start summarizing the conversation.", "role": "user"})
                context_summary = await RetryRunner.run(context_management_agent, input_items)
                feedback_message = f"""
                You are at iteration {iteration_count} of {max_iterations} working on the following task: {user_request}.
                The summarized context of the conversation is: {context_summary}
                Please address this feedback: {evaluation_result.feedback}
                """
                input_items = [
                    {"content": feedback_message, "role": "developer"},
                    {"content": "user_request", "role": "user"}
                ]
                logging.info("Evaluator feedback appended for further refinement.")

        print(f"\n🔍 Evaluation Score: {evaluation_result.score}")
        logging.debug("Exiting pipeline.")
            
    except KeyboardInterrupt:
        logging.info("Operation cancelled by user (KeyboardInterrupt).")
        print("\nOperation cancelled by user. Exiting...")

    except Exception as general_error:
        logging.info(f"Unexpected error occurred: {general_error}")