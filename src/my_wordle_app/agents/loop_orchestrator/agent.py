from google.adk.agents import SequentialAgent, LoopAgent
from guess_strategy_agent.agent import guess_strategy_agent
from guess_word_agent.agent import guess_executor
from page_opener_agent.agent import web_pager_opener_agent
from manual_page_opener.agent import manual_wordle_opener_agent

my_loop_agent = LoopAgent(
    name="think_and_guess", 
    sub_agents=[guess_strategy_agent, guess_executor], 
    max_iterations=12,
)

root_agent = SequentialAgent(
    name="run_wordle_game",
    sub_agents=[manual_wordle_opener_agent, my_loop_agent]
)