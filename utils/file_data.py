class FileData:
    def __init__(self, file):
        self.data = f"{file.file_id}:{file.file_unique_id}"

    def get_data(self):
        return self.data
