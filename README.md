# Simple Text Analysis
Run a text analysis using word sentiment scores and a markov-chain

## Requirements
- [Python3](https://www.python.org/downloads/)

## Usage
### Training
```bash
python main.py train
```

### Run a sentence analysis
```bash
python main.py analyse "Is this program really working?"

# Sentence: «Is this program really working?»
# Analysis: {'is_assert': 0, 'is_negative': 0, 'is_neutral': 1, 'is_positive': 0, 'is_question': 1, 'is_request': 1, 'object': '', 'object_is_human': 0, 'subject': 'this', 'subject_is_human': 0, 'verb': 'Is'}
```

Start the program:
python main.py "this is the sentence."

## Author(s)
- [@afranck64](https://github.com/afranck64)