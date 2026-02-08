FROM python:3.11-slim

# Install tmux and blessed
RUN apt-get update && apt-get install -y tmux && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir blessed

WORKDIR /app
COPY ./src .
COPY peers.txt .

ENV PYTHONUNBUFFERED=1

# Start a tmux session named "peer", run the script, and stay alive
#CMD ["sh", "-c", "tmux new-session -d -s peer 'python main.py --id $ID --port $PORT --peers peers.txt --log $LOG'; tmux attach-session -t peer"]
CMD ["sh", "-c", "tmux new-session -d -s peer 'python main.py'; tmux attach-session -t peer"]