from datasets import load_dataset
from transformers import AutoTokenizer

DATASET = 'hackathon-pln-es/spanish-to-quechua'
MODEL_NAME = 'facebook/xglm-564M'
SEQ_LEN   = 32

def getDataset():

    print(f'\nin getDataset')

    #data and tokenizer
    data = load_dataset(DATASET)
    tokenizer = getTokenizer(MODEL_NAME)	

    print(data)

    #split data
    # data = data["train"].train_test_split(test_size=.2, seed=1)

    data = data.map( preprocess,
                    # batched = True,
                    # num_proc = 4,
                    fn_kwargs = {'tokenizer' : tokenizer},
                    remove_columns = data['train'].column_names
                    )

    lm_dataset = data.map(group_texts, 
                        batched=True,
                        num_proc=4,
                        fn_kwargs = {'block_size' : SEQ_LEN } )
    print(lm_dataset)

    return lm_dataset

def getTokenizer(TOKENIZER):
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER)
    # tokenizer.pad_token = tokenizer.eos_token
    return tokenizer
		

def preprocess(data_row, tokenizer):
	return tokenizer(data_row['qu'])

def group_texts(examples, block_size):
	# Concatenate all texts.
	concatenated_examples = {k: sum(examples[k], []) for k in examples.keys()}
	total_length = len(concatenated_examples[list(examples.keys())[0]])
	# We drop the small remainder, we could add padding if the model supported it instead of this drop, you can
	# customize this part to your needs.

	# if total_length >= block_size:
	total_length = (total_length // block_size) * block_size
	
	# Split by chunks of block_size.
	result = {
		k: [t[i : i + block_size] for i in range(0, total_length, block_size)]
		for k, t in concatenated_examples.items()
	}

	# labels because the model expects the argument to be named labels
	result["labels"] = result["input_ids"].copy()
	# del result['input_ids']
	return result