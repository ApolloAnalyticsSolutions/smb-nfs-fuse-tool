import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor

logging.basicConfig(filename='logs/machine_learning.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def prepare_data(performance_data, target_values):
    """
    Prepare the data for the machine learning model.
    """
    try:
        # Convert the performance data to a pandas DataFrame
        data = pd.DataFrame([performance_data])

        # Separate the features and target variables
        X = data[['nfs_read_throughput', 'nfs_write_throughput', 'file_size']]
        y = np.array([target_values])  # Use the provided target values

        return X, y
    except Exception as e:
        logging.error(f"Error in prepare_data: {e}")
        return None, None

def train_model(X, y):
    """
    Train the linear regression model.
    """
    try:
        model = MultiOutputRegressor(GradientBoostingRegressor())
        model.fit(X, y)
        return model
    except Exception as e:
        logging.error(f"Error in train_model: {e}")
        return None

def recommend_configuration(performance_data, target_values):
    """
    Recommend configuration settings based on the performance data.
    """
    try:
        X, y = prepare_data(performance_data, target_values)
        if X is None or y is None:
            raise ValueError("Failed to prepare data")

        model = train_model(X, y)
        if model is None:
            raise ValueError("Failed to train model")

        recommended_config = model.predict(X)[0]

        return {
            "nfs_rsize": int(recommended_config[0]),
            "nfs_wsize": int(recommended_config[1])
        }
    except Exception as e:
        logging.error(f"Error in recommend_configuration: {e}")
        return {}

# Example usage
if __name__ == "__main__":
    example_data = {
        "nfs_read_throughput": 75.0,
        "nfs_write_throughput": 50.0,
        "file_size": 12
    }

    recommended_config = recommend_configuration(example_data, [5, 7])
    print(recommended_config)
