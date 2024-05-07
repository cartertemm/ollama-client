# OllamaClient

## Inspiration

I wrote this frontend because I've made quite the hobby out of running large language models locally, and [Ollama](https://ollama.com/) is awesome. It comes with a CLI good for one-off tasks... not so much long-form conversations.

Though there are many third party web-based frontends available, none of them feel particularly right to me (even if I can't exactly put a finger on why). Some on account of accessibility issues, others convenience or speed. Really I'm just out of practice using an IDE and my Copilot trial was about to expire, so this is the result of an afternoon trying to determine how well AI is able to fit into my workflow. I hope this app is useful to others and ends up being more than that.

## Getting started

Firstly, you need python (3.7 or greater) installed on your computer and added to path.

Once that's done, follow the [Ollama quickstart](https://github.com/ollama/ollama/blob/main/README.md#quickstart). For the sake of this frontend, there are a few things you will need to do.

Download and install Ollama onto your operating system. You can obtain installers from the link above.

note: This application assumes your machine has the relevant hardware (graphics and RAM) to run local models. Ollama provides a list of [supported GPUs](https://github.com/ollama/ollama/blob/main/docs/gpu.md) for your reference.

Pull a model so we have something to work with:

```
ollama pull llama3
```

Clone this repository:

```
git clone https://github.com/cartertemm/ollama-client/ollama-client.git
```

Change to the directory:

```
cd ollama-client
```

Install the requirements:

```
pip install -r requirements.py
```

Run the program:

```
python client.py
```

You will first see a dialog asking for the connection information. Proceed with the defaults unless you deliberately changed these. click OK, and after a second or so a dialog will pop up prompting you to choose a model. Then you'll be lead to the chat interface. Of course, it is possible to change the model on the fly at any point throughout a conversation by clicking manage models, or pressing alt+m.
