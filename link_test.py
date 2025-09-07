# link_example.py
from textual.app import App, ComposeResult
from textual.widgets import Markdown

class LinkApp(App):
    def compose(self) -> ComposeResult:
        # A Markdown link: [label](https://url)
        yield Markdown(
            "# Hello Textual!\n\n"
            "Click this [OpenAI](https://openai.com) link."
        )

if __name__ == "__main__":
    LinkApp().run()

