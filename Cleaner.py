import os


class Cleaner:
    "Helper class for cleaning directory after bot disconnects"
    @staticmethod
    def empty_songs() -> None:
        """Removes all .webm files from the "ytdl" directory in the current working directory"""
        dir_path = os.path.join(os.getcwd(), "ytdl")

        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)

            if file_name.endswith(".webm"):
                os.remove(file_path)
