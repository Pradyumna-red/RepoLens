"""
Main application entry point.
"""
import os
import sys
from utils import helper_function
from config import settings

def main():
    print("Starting application...")
    helper_function()
    print(f"Config: {settings}")

if __name__ == "__main__":
    main()
