import csv

def update_attribute(obj, attribute, new_value, csv_file, id_column="id"):
    """
    Updates an attribute of an object and ensures it is also updated in the CSV file.

    :param obj: The object whose attribute is being updated.
    :param attribute: The name of the attribute to update (as a string).
    :param new_value: The new value for the attribute.
    :param csv_file: The path to the CSV file where the update should be made.
    :param id_column: The column name that uniquely identifies the object in the CSV file.
    """
    if not hasattr(obj, attribute):
        raise AttributeError(f"Object does not have attribute '{attribute}'.")

    # Update the object attribute
    setattr(obj, attribute, new_value)

    # Read CSV file and update the corresponding row
    updated_rows = []
    with open(csv_file, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        for row in reader:
            if str(row[id_column]) == str(getattr(obj, id_column)):  # Find the matching row
                row[attribute] = new_value  # Update the attribute in CSV
            updated_rows.append(row)

    # Write back the updated data
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)



def bulk_update(objects, attributes, new_values, csv_file, id_column="id"):
    """
    Updates multiple attributes for multiple objects and ensures changes are saved in the CSV file.

    :param objects: A list of objects to update.
    :param attributes: A list of attribute names to update.
    :param new_values: A list of new values corresponding to the attributes.
    :param csv_file: The path to the CSV file.
    :param id_column: The column name that uniquely identifies objects in the CSV.
    """
    if len(objects) != len(attributes) or len(objects) != len(new_values):
        raise ValueError("Mismatched lengths of objects, attributes, and new_values lists.")

    # Update object attributes
    for obj, attr, value in zip(objects, attributes, new_values):
        if not hasattr(obj, attr):
            raise AttributeError(f"Object {obj} does not have attribute '{attr}'.")
        setattr(obj, attr, value)

    # Read CSV file and update the corresponding rows
    updated_rows = []
    with open(csv_file, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        for row in reader:
            for obj, attr, value in zip(objects, attributes, new_values):
                if str(row[id_column]) == str(getattr(obj, id_column)):
                    row[attr] = value
            updated_rows.append(row)

    # Write back the updated data
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)


def print_object(obj):
    """
    Prints all attributes of an object.

    :param obj: The object to inspect.
    """
    attributes = vars(obj)
    for key, value in attributes.items():
        print(f"{key}: {value}")
