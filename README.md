# StorytellerNAO

## Setup
### Main Folder
1. Create a virtual environment for the main folder using Python 2.7:
  ```bash
  python2.7 -m venv main_venv
  ```
2. Activate the virtual environment:
  - For macOS/Linux:
    ```bash
    source main_venv/bin/activate
    ```
  - For Windows:
    ```bash
    main_venv\Scripts\activate
    ```
3. Install the required dependencies from the `requirements.txt` file:
  ```bash
  pip install -r requirements.txt
  ```

### OpenAI Folder
1. Create a virtual environment for the openai folder using Python 3.8+:
  ```bash
  python3.8 -m venv openai_venv
  ```
2. Activate the virtual environment:
  - For macOS/Linux:
    ```bash
    source openai_venv/bin/activate
    ```
  - For Windows:
    ```bash
    openai_venv\Scripts\activate
    ```
3. Install the required dependencies from the `requirements.txt` file:
  ```bash
  pip install -r requirements.txt
  ```

4. Add your OpenAI key:
  ```bash
  export OPENAI_API_KEY="YOUR_KEY"
  ```

## Usage
- Make sure to activate the respective virtual environment before working in each folder.
- Install the required dependencies using pip or any package manager of your choice.

1. Run the OpenAI server:
  ```bash
  cd openai_server
  source venv/bin/activate
  python3 server.py
  ```

2. Run the app
  ```bash
  source venv/bin/activate
  python2 main.py
  ```

## License
This project is licensed under the [MIT License](LICENSE).