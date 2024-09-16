"""
Prompt Manager

Tested with:
jinja2==3.1.3
python-frontmatter==1.1.0

Source: https://www.youtube.com/watch?v=Qddc_DNo9qY
Prompt Management 101 - Full Guide for AI Engineers by Dave Ebbelaar

"""

from pathlib import Path

import frontmatter
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateError, meta


class PromptManager:
    _env = None

    @classmethod
    def _get_env(cls, templates_dir="prompts/templates"):
        templates_dir = Path(__file__).parent.parent / templates_dir
        if cls._env is None:
            cls._env = Environment(
                loader=FileSystemLoader(templates_dir),
                undefined=StrictUndefined,
            )
        return cls._env

    @staticmethod
    def get_prompt(template, **kwargs):
        env = PromptManager._get_env()
        template_path = f"{template}.j2"
        with open(env.loader.get_source(env, template_path)[1]) as file:
            post = frontmatter.load(file)

        template = env.from_string(post.content)
        try:
            return template.render(**kwargs)
        except TemplateError as e:
            raise ValueError(f"Error rendering template: {str(e)}")

    @staticmethod
    def get_template_info(template):
        env = PromptManager._get_env()
        template_path = f"{template}.j2"
        with open(env.loader.get_source(env, template_path)[1]) as file:
            post = frontmatter.load(file)

        ast = env.parse(post.content)
        variables = meta.find_undeclared_variables(ast)

        return {
            "name": template,
            "description": post.metadata.get("description", "Description missing"),
            "author": post.metadata.get("author", "Unknown"),
            "version": post.metadata.get("version", "Unknown"),
            "variables": list(variables),
            "frontmatter": post.metadata,
        }


if __name__ == "__main__":
    frontmatter.load("./templates/welcome_msg.j2")

    wlc_msg = PromptManager.get_prompt("welcome_msg", user_name="Joe")
    print(wlc_msg)

    wlc_msg = PromptManager.get_prompt("welcome_msg")
    print(wlc_msg)

    wlc_msg = PromptManager.get_prompt("welcome_msg", user_name="Joe test")
    print(wlc_msg)

    template_info = PromptManager.get_template_info("welcome_msg")
    print(template_info)

    # system prompts
    system_msg = PromptManager.get_prompt("system_msg")
    print(system_msg)

    system_msg = PromptManager.get_prompt("system_msg", context="context")
    print(system_msg)
