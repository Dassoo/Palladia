from agno.agent import RunResponse

def trim_response(response: RunResponse) -> RunResponse:
    """
    Custom trim for 'thudm/glm-4.1v-9b-thinking' model
    """
    content = str(response.content).strip()
    
    if content.startswith("<answer>"):
        content = content[8:]

    response.content = content.strip()
    
    return response
