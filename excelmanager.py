import os 
import pandas as pd

class ExcelManager:
    def __init__(self, filename: str = "student_data.xlsx"):
        self.filename = filename

    def save(self, student_library: list[list]) -> pd.DataFrame:
        columns = ["prenom", "nom", "date", "etat", "tempRetard"]
        df = pd.DataFrame(student_library, columns=columns)

        if os.path.isfile(self.filename):
            existing_data = pd.read_excel(self.filename)
            for _, row in df.iterrows():
                match_found = False
                for i, existing_row in existing_data.iterrows():
                    if (
                        row["prenom"] == existing_row["prenom"]
                        and row["nom"] == existing_row["nom"]
                        and row["date"] == existing_row["date"]
                    ):
                        existing_data.loc[i] = row
                        match_found = True
                        break
                if not match_found:
                    existing_data = pd.concat([existing_data, row.to_frame().T], ignore_index=True)
            existing_data.to_excel(self.filename, index=False)
            return existing_data
        else:
            df.to_excel(self.filename, index=False)
            return df
