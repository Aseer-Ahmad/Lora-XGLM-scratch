import torch
import datasets

from transformers import AutoModelForCausalLM, TrainingArguments, Trainer
from dataloader import getDataset
from functools import partial
import time

MODEL_NAME = 'facebook/xglm-564M'


class LoRALayer(torch.nn.Module):
    def __init__(self, in_dim, out_dim, rank, alpha):
        super().__init__()
        std_dev = 1 / torch.sqrt(torch.tensor(rank).float())
        self.A = torch.nn.Parameter(torch.randn(in_dim, rank) * std_dev)
        self.B = torch.nn.Parameter(torch.zeros(rank, out_dim))
        self.alpha = alpha

    def forward(self, x):
        x = self.alpha * (x @ self.A @ self.B)
        return x

class LinearWithLoRA(torch.nn.Module):
    def __init__(self, linear, rank, alpha):
        super().__init__()
        self.linear = linear
        self.lora = LoRALayer(
            linear.in_features, linear.out_features, rank, alpha
        )

    def forward(self, x):
        return self.linear(x) + self.lora(x)
    

def get_lora_model(model):
    # default hyperparameter choices
    lora_r = 8
    lora_alpha = 16
    lora_dropout = 0.05
    lora_query = True
    lora_key = True
    lora_value = True
    lora_projection = False
    lora_mlp = False
    lora_head = False
  
    assign_lora = partial(LinearWithLoRA, rank=lora_r, alpha=lora_alpha)

    for layer in model.model.layers:
        if lora_query:
            layer.self_attn.q_proj = assign_lora(layer.self_attn.q_proj)
        if lora_key:
            layer.self_attn.k_proj = assign_lora(layer.self_attn.k_proj)
        if lora_value:
            layer.self_attn.v_proj = assign_lora(layer.self_attn.v_proj)
        if lora_projection:
            layer.self_attn.out_proj = assign_lora(layer.self_attn.out_proj)
        if lora_mlp:
            layer.fc1 = assign_lora(layer.fc1)
            layer.fc2 = assign_lora(layer.fc2)

    if lora_head:
        model.model.lm_head = assign_lora(model.model.lm_head)

    return model

def train_XGLM_lora():
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    lora_model = get_lora_model(model)
    lm_dataset = getDataset()
    train_XGLM(lora_model, lm_dataset, "xglm_lora")
    

def train_XGLM(model, lm_dataset, output_dir):
    
    training_args = TrainingArguments(
    output_dir=output_dir,
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    weight_decay=0.01,
    push_to_hub=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=lm_dataset["train"],
        eval_dataset=lm_dataset["test"],
        # data_collator=data_collator,
    )

    st = time.time()
    trainer.train()
    et = time.time()

    print(f"total training time : {(et - st)} sec.")


if __name__ == '__main__':
    train_XGLM_lora()