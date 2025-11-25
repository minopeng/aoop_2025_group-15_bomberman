# Save as: setup_new_model.py
import os
import tensorflow as tf
from tensorflow.keras import layers, models

def create_connect4_model(output_path="models/connect4_v1.keras"):
    print(f"🧠 Initializing new Neural Network for Connect-4...")
    
    # Check if file already exists to prevent accidental overwrite
    if os.path.exists(output_path):
        print(f"⚠️  WARNING: {output_path} already exists!")
        choice = input("Overwrite? (y/n): ")
        if choice.lower() != 'y':
            print("Operation cancelled.")
            return

    # Standard CNN for Board Games (Input: 15x15 board)
    input_shape = (15, 15, 1) 

    model = models.Sequential([
        # Layer 1: Detect small patterns (lines of 2 or 3)
        layers.Conv2D(64, (3, 3), padding='same', activation='relu', input_shape=input_shape),
        # Layer 2: Detect larger patterns
        layers.Conv2D(128, (3, 3), padding='same', activation='relu'),
        # Layer 3: Complex board awareness
        layers.Conv2D(128, (3, 3), padding='same', activation='relu'),
        
        layers.Flatten(),
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.3), 
        layers.Dense(225, activation='softmax') # 15*15 = 225 possible moves
    ])

    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    model.save(output_path)
    print(f"✅ Success! New model saved to: {output_path}")

if __name__ == "__main__":
    create_connect4_model()