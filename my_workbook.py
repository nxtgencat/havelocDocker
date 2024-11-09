from openpyxl import load_workbook


def file_data_extract(file_path):
    # Load the workbook and select the active sheet
    workbook = load_workbook(file_path)
    sheet = workbook.active

    # Define the list of keywords to check for
    keywords = ['reg no', 'reg', 'roll no', 'roll', 'registration']

    # Iterate through the header row to find the column containing any of the keywords
    reg_column_index = None
    for col_index, col in enumerate(sheet.iter_cols(min_row=1, max_row=1, values_only=True), start=1):
        for cell in col:
            if cell and any(keyword in str(cell).lower() for keyword in keywords):
                reg_column_index = col_index
                break
        if reg_column_index:
            break

    # If the column is found, extract and return the entire column (excluding the header)
    if reg_column_index:
        column_data = []
        for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=reg_column_index, max_col=reg_column_index,
                                   values_only=True):
            column_data.append(str(row[0]))  # Convert each value to string and append to list

        # Join the list into a comma-separated string
        return ', '.join(column_data)
    else:
        return "Column with specified keywords not found."
