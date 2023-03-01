
# gpt_context_bot  
simple gpt3 bot saving context  
  
To run:  

make ".env" file with API_KEY and BOT_TOKEN  

    API_KEY = "..."
    BOT_TOKEN = "..."

Debian:  
  

    sudo apt update  
  
	sudo  apt-get install git python3-venv  
  
	git clone https://github.com/deadulya/gpt_context_bot.git  
  
	python3 -m venv ./venv  
  
	source ./venv/bin/activate  
  
	pip install -r requirements  
  
	python context_bot.py

Or run in background:

	python context_bot.py &

