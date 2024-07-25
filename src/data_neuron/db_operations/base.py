from abc import ABC, abstractmethod


class DatabaseOperations(ABC):
    @abstractmethod
    def get_table_list(self):
        pass

    @abstractmethod
    def get_table_info(self, table_name):
        pass

    @abstractmethod
    def execute_query(self, query: str) -> str:
        pass

    @abstractmethod
    def get_schema_info(self) -> str:
        pass

    def handle_error(self, operation: str, error: Exception) -> str:
        error_type = type(error).__name__
        error_message = str(error)

        if "connection" in error_message.lower():
            return f"Connection error during {operation}: {error_message}. Please check your database credentials and connection settings."
        elif isinstance(error, ImportError):
            return f"Missing database driver for {operation}: {error_message}. Please install the required database driver."
        else:
            return f"Error during {operation}: [{error_type}] {error_message}"
