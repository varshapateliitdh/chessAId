from textwrap import dedent

from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.schema import AIMessage, HumanMessage
from langchain.tools.render import format_tool_to_openai_function
from langchain_openai.chat_models import AzureChatOpenAI  # Azure LLM class
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable

from chessAId.langserve.tools import get_tools


def _format_chat_history(chat_history: list[tuple[str, str]]):
    buffer = []
    for human, ai in chat_history:
        buffer.append(HumanMessage(content=human))
        buffer.append(AIMessage(content=ai))
    return buffer


def get_agent() -> Runnable:
    """Get Langchain Runnable for analyzing and modifying board."""
    system_message = """
    You are a seasoned chess instructor teaching a student.  
    Your role is to help them learn chess while keeping the session engaging and enjoyable.  

    You will receive game history {game_history}, which contains the moves of the game so far.  
    Always interpret game history accurately before responding.  

    Capabilities:  
    - Analyze live or past games using game history.  
    - If asked for the next move, suggest one clearly in algebraic notation (e.g., Nf3, e4), based only on game history.  
    - Do not invoke external tools.  

    Style:  
    - Keep explanations concise (20 words or fewer).  
    - You may respond to greetings naturally.  
    - If asked something unrelated to chess, reply:  
    "That's outside our chess discussion. Let's focus on the game!"  

    """
    tools = get_tools()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", dedent(system_message)),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{user_message}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Create AzureChatOpenAI client with credentials set in code
    llm = AzureChatOpenAI(
        azure_endpoint=# replace with your actual endpoint
        api_key=# replace with your API key
        deployment_name=# replace with your deployment name
        api_version=# or the version you're using
        temperature=0,
    )

    llm_with_tools = llm.bind(
        functions=[format_tool_to_openai_function(tool) for tool in tools]
    )

    agent = (
        {
            "user_message": lambda x: x["user_message"],
            "chat_history": lambda x: _format_chat_history(x["chat_history"]),
            "game_history": lambda x: x["game_history"],
            "agent_scratchpad": lambda x: format_to_openai_function_messages(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    )

    return agent
