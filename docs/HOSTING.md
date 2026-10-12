# Hosting options (verify limits before relying on them)

| Option | Good for | Catch |
|---|---|---|
| **Kaggle notebook (GPU T4)** | Best now: free GPU, public Gradio link | Sessions time out; weekly GPU quota; Internet must be ON |
| **Colab (T4)** | Same idea | Session limits, disconnects |
| **Hugging Face Spaces** | Permanent URL | Free CPU is 2 vCPU/16 GB, but docs now say Gradio/Docker Spaces need a paid plan; ZeroGPU Gradio Spaces are free for personal accounts; free Spaces sleep |
| **Oracle Cloud Always Free (ARM VM)** | Always-on, lots of RAM | Signup friction, Linux setup, no GPU |
| **Render / Railway free** | Tiny demos | ~512 MB RAM: too small for these models |

**Privacy:** unpublished theses should stay on private links; set `APP_PASS` for a password (username `user`). Online source checks send phrases to outside services; disable them for sensitive work.
