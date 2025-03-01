from typing import Tuple, Optional, Union

import torch.nn as nn
from torch import Tensor


from flambe.nn import Embedder, Module


class LanguageModel(Module):
    """Implement an LanguageModel model for sequential classification.

    This model can be used to language modeling, as well as other
    sequential classification tasks. The full sequence predictions
    are produced by the model, effectively making the number of
    examples the batch size multiplied by the sequence length.

    """

    def __init__(self,
                 embedder: Embedder,
                 output_layer: Module,
                 dropout: float = 0,
                 pad_index: int = 0,
                 tie_weights: bool = False,
                 tie_weight_attr: str = 'embedding') -> None:
        """Initialize the LanguageModel model.

        Parameters
        ----------
        embedder: Embedder
            The embedder layer
        output_layer : Decoder
            Output layer to use
        dropout : float, optional
            Amount of droput between the encoder and decoder,
            defaults to 0.
        pad_index: int, optional
            Index used for padding, defaults to 0
        tie_weights : bool, optional
            If true, the input and output layers share the same weights
        tie_weight_attr: str, optional
            The attribute to call on the embedder to get the weight
            to tie. Only used if tie_weights is ``True``. Defaults
            to ``embedding``. Multiple attributes can also be called
            by adding another dot: ``embeddings.word_embedding``.

        """
        super().__init__()

        self.embedder = embedder
        self.output_layer = output_layer
        self.drop = nn.Dropout(dropout)

        self.pad_index = pad_index
        self.tie_weights = tie_weights

        if tie_weights:
            module = self.embedder
            for attr in tie_weight_attr.split('.'):
                module = getattr(module, attr)
            self.output_layer.weight = module.weight

    def forward(self,
                data: Tensor,
                target: Optional[Tensor] = None) -> Union[Tensor, Tuple[Tensor, Tensor]]:
        """Run a forward pass through the network.

        Parameters
        ----------
        data: Tensor
            The input data

        Returns
        -------
        Union[Tensor, Tuple[Tensor, Tensor]]
            The output predictions of shape seq_len x batch_size x n_out

        """
        encoding, _ = self.embedder(data)
        mask = (data != self.pad_index).float()

        if target is not None:
            # Flatten to compute loss across batch and sequence
            flat_mask = mask.view(-1).byte()
            flat_encodings = encoding.view(-1, encoding.size(2))[flat_mask]
            flat_targets = target.view(-1)[flat_mask]
            flat_pred = self.output_layer(self.drop(flat_encodings))
            return flat_pred, flat_targets
        else:
            pred = self.output_layer(self.drop(encoding))
            return pred
