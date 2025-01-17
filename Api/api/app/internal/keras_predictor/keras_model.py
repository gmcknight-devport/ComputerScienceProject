from keras import Sequential
from keras.activations import relu, sigmoid, tanh, softmax, elu, softsign, softplus, exponential
from keras.layers import Dropout, Dense, LSTM, Conv1D, SimpleRNN, Bidirectional, GRU
from typing import Optional, Type
from pydantic import BaseModel
import numpy as np
from sklearn.preprocessing import MinMaxScaler


models = {"LSTM": LSTM, "SimpleRNN": SimpleRNN, "Bidirectional": Bidirectional, "Conv1D": Conv1D, "GRU": GRU}
activation_functions = {"relu": relu, "sigmoid": sigmoid, "tanh": tanh, "softmax": softmax, "elu": elu,
                        "softsign": softsign, "softplus": softplus, "exponential": exponential}


class ModelOptions(BaseModel):
    iterations: Optional[int] = 1
    epochs: Optional[int] = 20
    num_inputs: Optional[object] = 40
    batch_size: Optional[int] = 10
    dropout: Optional[float] = 0.1
    optimiser: Optional[str] = "adam"
    loss: Optional[str] = "mse"


def create_model(model_name: type, model_options: ModelOptions, input_shape: object, activation_function: type,
                 scale: MinMaxScaler, train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray, test_y: np.ndarray):

    # Check activation function exists in array:
    if activation_function not in activation_functions.keys():
        activation_function = activation_functions.get("tanh")
    else:
        activation_function = activation_functions.get(activation_function)

    # Create sequential model
    model = Sequential()

    # Set batch size if it's None
    if model_options.batch_size is None:
        model_options.batch_size = len(train_x[0]) * 0.025
        model_options.batch_size = round(model_options.batch_size)

    # loop iterations 1 less than parameter to include return_sequences
    for i in range(model_options.iterations - 1):
        model.add(model_name(model_options.num_inputs, input_shape=input_shape, activation=activation_function,
                             return_sequences=True))
        model.add(Dropout(model_options.dropout))

    # Add last layer of model with dropout and dense
    model.add(model_name(model_options.num_inputs, input_shape=input_shape, activation=activation_function))
    model.add(Dropout(0.1))
    model.add(Dense(1, activation=activation_function))

    # Compile model
    model.compile(
        optimizer=model_options.optimiser,
        loss=model_options.loss,
        metrics=['accuracy'])

    # Fit model
    model.fit(train_x, train_y, epochs=model_options.epochs, batch_size=model_options.batch_size, verbose=1)

    # Convert values to float from numpy.int32
    test_x = test_x.astype(float)
    test_y = test_y.astype(float)

    # Make test predictions
    test_predictions = model.predict(test_x)

    # Invert scaling
    test_predictions = scale.inverse_transform(test_predictions)
    test_y = scale.inverse_transform([test_y])

    # Future Predictions
    prediction_days = 10
    predictions = np.array([])

    # Get proper shape
    final_test_data = test_y
    data_to_add = train_y[len(train_y) - 1:]
    final_test_data = np.insert(final_test_data, 0, data_to_add)
    final_test_data = np.reshape(final_test_data, (1, final_test_data.shape[0]))

    # Get most recent Close value and prepare for prediction
    last_val = final_test_data
    last_val = np.reshape(last_val, (last_val.shape[0], last_val.shape[1], 1))
    p = last_val

    # Predict next close price based on previous
    for i in range(prediction_days):
        p = model.predict(p)
        p = np.reshape(p, (1, p.shape[0], p.shape[1]))
        predictions = np.append(predictions, p[len(p)-1:])

    # Reshape and scale predictions
    predictions = np.reshape(predictions, (predictions.shape[0], 1))
    predictions = scale.inverse_transform(predictions)

    return test_predictions, test_y, predictions
