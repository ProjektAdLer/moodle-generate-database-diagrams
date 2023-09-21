import xml.etree.ElementTree as ET
import sys


def apply_custom_fixes(sql_statements):
    fixed_statements = []
    for statement in sql_statements:
        # Apply the fix to change FOREIGN KEY definition for gradeitemid
        fixed_statement = statement.replace(
            "FOREIGN KEY (gradeitemid, courseid) REFERENCES grade_items(id, courseid)",
            "FOREIGN KEY (gradeitemid) REFERENCES grade_items(id)"
        )
        # same but for earlier versions of moodle
        fixed_statement = fixed_statement.replace(
            "FOREIGN KEY (gradeitemid,courseid) REFERENCES grade_items(id,courseid)",
            "FOREIGN KEY (gradeitemid) REFERENCES grade_items(id)"
        )

        # Add more custom fixes here, if needed
        # fixed_statement = fixed_statement.replace("some_old_text", "some_new_text")

        fixed_statements.append(fixed_statement)
    return fixed_statements

# Convert XMLDB type to SQL type
def get_sql_type(xmldb_type, length, decimals=0):
    if xmldb_type == "int":
        if int(length) <= 2:
            return f"TINYINT({length})"
        elif int(length) <= 4:
            return f"SMALLINT({length})"
        elif int(length) <= 6:
            return f"MEDIUMINT({length})"
        elif int(length) <= 9:
            return f"INT({length})"
        else:
            return f"BIGINT({length})"
    elif xmldb_type == "text":
        return "TEXT"
    elif xmldb_type == "char":
        return f"VARCHAR({length})"
    elif xmldb_type == "number":
        return f"FLOAT({length},{decimals})" if decimals else f"FLOAT({length})"
    elif xmldb_type == "float":
        if int(decimals) < 6:
            return "FLOAT"
        else:
            return f"DOUBLE"

    else:
        sys.stderr.write(f"Error: Unknown type '{xmldb_type}' encountered.\n")
        sys.exit(1)

# Function to handle the indexes
def handle_indexes(indexes_element):
    indexes = []
    for index in indexes_element.findall('INDEX'):
        index_name = index.get('NAME')
        unique = 'UNIQUE' if index.get('UNIQUE') == "true" else ''
        fields = index.get('FIELDS')
        # Added backticks around index_name
        indexes.append(f"{unique} INDEX `{index_name}` ({fields})")
    return indexes

# Add quotes around default values if they are strings
def quote_default(default_value):
    try:
        int(default_value)
        return default_value
    except ValueError:
        return f"'{default_value}'"

# Read a list of XMLDB files and generate SQL CREATE TABLE statements
def convert_xmldb_to_sql(file_list):
    sql_statements = ["-- Disable foreign key checks\nSET foreign_key_checks = 0;"]

    with open(file_list, 'r') as f:
        files = f.readlines()

    for file in files:
        file = file.strip()
        tree = ET.parse(file)
        root = tree.getroot()

        for table in root.find('TABLES').findall('TABLE'):
            table_name = table.get('NAME')
            comment = table.get('COMMENT', '')
            table_comment = "COMMENT '" + comment.replace("'", "''") + "'" if comment else ""

            fields = []
            for field in table.find('FIELDS').findall('FIELD'):
                field_name = field.get('NAME')
                field_type = field.get('TYPE')
                field_length = field.get('LENGTH', '')
                field_comment = "COMMENT '" + field.get('COMMENT', '').replace("'", "''") + "'" if field.get('COMMENT') else ""
                field_notnull = "NOT NULL" if field.get('NOTNULL') == "true" else ""
                field_default = f"DEFAULT {quote_default(field.get('DEFAULT'))}" if field.get('DEFAULT') else ""
                field_auto_increment = "AUTO_INCREMENT" if field.get('SEQUENCE') == "true" else ""

                field_decimals = field.get('DECIMALS', 0)
                sql_type = get_sql_type(field_type, field_length, field_decimals)

                field_line = f"{field_name} {sql_type} {field_notnull} {field_default} {field_auto_increment} {field_comment}".strip()
                fields.append(field_line)

            keys = []
            for key in table.find('KEYS').findall('KEY'):
                key_name = key.get('NAME')
                key_type = key.get('TYPE').upper()
                key_fields = key.get('FIELDS')
                ref_table = key.get('REFTABLE')
                ref_fields = key.get('REFFIELDS')
                if key_type == "PRIMARY":
                    keys.append(f"PRIMARY KEY ({key_fields})")
                elif key_type == "UNIQUE":
                    keys.append(f"UNIQUE ({key_fields})")  # Add this line to handle unique keys
                elif ref_table and ref_fields:
                    keys.append(f"FOREIGN KEY ({key_fields}) REFERENCES {ref_table}({ref_fields})")
            # Handle Indexes
            indexes_element = table.find('INDEXES')
            if indexes_element is not None:
                indexes = handle_indexes(indexes_element)
                fields += indexes  # Append the index statements to the fields list


            fields_and_keys = ",\n".join(fields + keys)
            create_table_statement = f"CREATE TABLE {table_name} (\n{fields_and_keys}\n) {table_comment};"

            if comment:
                create_table_statement = f"-- {comment}\n" + create_table_statement

            sql_statements.append(create_table_statement)

    sql_statements = apply_custom_fixes(sql_statements)
    sql_statements.append("-- Enable foreign key checks\nSET foreign_key_checks = 1;")
    return sql_statements

if __name__ == "__main__":
    file_list = "list_of_xmldb_files.txt"  # Replace with your file that contains a list of XMLDB file paths
    sql_statements = convert_xmldb_to_sql(file_list)

    for sql in sql_statements:
        print(sql)
        print()