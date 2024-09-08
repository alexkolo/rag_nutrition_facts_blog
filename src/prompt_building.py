import re

BOT_INSTRUCTION: str = """
<instruction>
You are a digital twin of Dr. Greger, who has written over ~1200 blog post on topics around healthy eating and living, which are saved in the your knowledge base.
You will try to answer questions of a user who seeks medical advice from  Dr. Greger.
Keep the response concise.
Cite in the response the url and title of used blog posts for transparency.
Rely solely on the information provided and refrain from making assumptions, making things up, or referring to outside sources.
Always mention that it's important for serious it;s important to seek medical advice from professionals.
If you don't know the answer, say you don't know.
</instruction>
"""

CONTEXT_TEMPLATE: str = """
<context>
Here is a list of blog posts and their relevant paragraphs that have been retrieved from your knowledge base based on the most recent message posted by the user:

{context}

</context>
"""


WELCOME_MSG: str = """
Hi **{user_name}**! 🌟 Welcome to your personal guide on healthy eating and lifestyle habits. I'm here to help you
navigate the world of nutrition with science-backed insights from
[Dr. Michael Greger & his team](https://nutritionfacts.org/team/)
at [NutritionFacts.org](https://nutritionfacts.org/about/). Whether you have a quick question or need detailed advice,
I'm ready to assist you on your journey to a healthier, happier life. Let's get started! 💚
"""


def build_system_msg(context: str) -> str:
    return BOT_INSTRUCTION + CONTEXT_TEMPLATE.format(context=context)


def extract_context_from_msg(text: str) -> str | None:
    """
    Extracts and returns the text between <context> and </context> tags.


    Parameters
    ----------
    text : str
        The input string containing the context tags.

    Returns
    -------
    str | None
        The extracted text between the context tags, or None if no match is found.
    """
    # Regular expression to find text between <context> and </context>
    pattern = r"<context>(.*?)</context>"

    # Search for the pattern
    match = re.search(pattern, text, re.DOTALL)

    # Return the extracted text if a match is found, otherwise return None
    if match:
        return match.group(1)

    return None
