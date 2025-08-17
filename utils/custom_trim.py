from agno.agent import RunResponse

def glm_trim(response: RunResponse) -> RunResponse:
    """
    Custom trim for 'z-ai/glm-4.5v' model extra verbose
    """
    content = str(response.content).strip()
    
    if content.startswith("<|begin_of_box|>"):
        content = content[16:]
    
    if content.endswith("<|end_of_box|>"):
        content = content[:-14]

    response.content = content.strip()
    
    return response


def grok_trim(response: RunResponse) -> RunResponse:
    """
    Custom trim for 'grok-4' model duplicate answers
    """
    content = str(response.content).strip()
    half = len(content) // 2
    first, second = content[:half], content[half:]
    response.content = first.strip() if first == second else text.strip()
    
    return response