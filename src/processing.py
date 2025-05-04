import numpy as np

def standardize_data(data, fields_to_standardize=None, per_feature=True):
    """Standardize data by subtracting mean and dividing by standard deviation.
    
    Args:
        data: Dictionary of arrays to standardize
        fields_to_standardize: List of keys in data to standardize
        per_feature: If True, standardize each feature separately
        
    Returns:
        Tuple of standardized data and dict of statistics used for standardization
    """
    standardized_data = {}
    stats = {}
    
    # If fields_to_standardize is None, standardize all fields
    if fields_to_standardize is None:
        fields_to_standardize = list(data.keys())

    for field in data:
        if field in fields_to_standardize:
            # Get the data to standardize
            field_data = data[field]
            
            # Initialize stats for this field
            stats[field] = {}
            
            # Standardize the field
            if per_feature:
                # Compute mean and std per feature
                mean = np.mean(field_data, axis=0)
                std = np.std(field_data, axis=0)
                
                # Avoid division by zero by adding epsilon to std where it's zero
                epsilon = 1e-10
                std = np.where(std < epsilon, epsilon, std)
                
                # Store stats
                stats[field]['mean'] = mean
                stats[field]['std'] = std
                
                # Apply standardization - need to ensure proper broadcasting
                # Shape handling for robust broadcasting
                reshaped_mean = mean.reshape(1, -1) if len(field_data.shape) > 1 else mean
                reshaped_std = std.reshape(1, -1) if len(field_data.shape) > 1 else std
                
                standardized_data[field] = (field_data - reshaped_mean) / reshaped_std
            else:
                # Compute global mean and std
                mean = np.mean(field_data)
                std = np.std(field_data)
                
                # Avoid division by zero
                if std < 1e-10:
                    std = 1e-10
                
                # Store stats
                stats[field]['mean'] = mean
                stats[field]['std'] = std
                
                # Apply global standardization
                standardized_data[field] = (field_data - mean) / std
        else:
            # Copy fields that don't need to be standardized
            standardized_data[field] = data[field]
    
    return standardized_data, stats