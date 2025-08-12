from agno.agent import RunResponse

def trim_response(response: RunResponse) -> RunResponse:
    """
    Custom trim for 'z-ai/glm-4.5v' model
    """
    content = str(response.content).strip()
    
    if content.startswith("<|begin_of_box|>"):
        content = content[16:]
    
    if content.endswith("<|end_of_box|>"):
        content = content[:-14]

    response.content = content.strip()
    
    return response
