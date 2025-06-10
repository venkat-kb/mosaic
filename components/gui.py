import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import os


class GrievanceManagementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Grievance Management System")
        self.root.geometry("1200x700")

        # Load case data from JSON file
        self.case_records = self.load_case_data()
        self.categories_data = self.load_categories_data()  # Load full category data
        self.departments = self.load_departments()
        self.current_department = "All Departments"

        self.setup_gui()
        self.populate_table()

    def load_case_data(self):
        """Load case records from case_data.json file, filtering for non-empty priority"""
        with open("test.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        # Filter cases with non-empty priority
        filtered_cases = []
        for case in data:
            priority = case.get("priority", "")
            if priority and str(priority).strip():
                filtered_cases.append(case)

        return filtered_cases

    def load_categories_data(self):
        """Load full categories data for keyword matching"""
        try:
            with open("categories_data.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading categories data: {e}")
            return []

    def load_departments(self):
        """Load departments from categories_data.json if available, otherwise use defaults"""
        try:
            with open("categories_data.json", "r") as f:
                data = json.load(f)

                # Since JSON is an array of category objects, extract names
                if isinstance(data, list):
                    dept_names = []
                    for item in data:
                        if isinstance(item, dict) and "name" in item:
                            dept_names.append(item["name"])
                    return ["All Departments"] + dept_names
                else:
                    # Fallback for other formats
                    return ["All Departments"] + list(data.keys())

        except Exception as e:
            print(f"Error loading departments: {e}")
            # Default departments if file not found or error occurs
            return [
                "All Departments",
                "Public Works",
                "Health Services",
                "Transportation",
                "Utilities",
                "Housing",
                "Environment",
                "Safety & Security",
                "Education",
                "Social Services",
            ]

    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Department filter
        ttk.Label(main_frame, text="Department:").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 10)
        )

        self.dept_var = tk.StringVar(value=self.current_department)
        dept_combo = ttk.Combobox(
            main_frame,
            textvariable=self.dept_var,
            values=self.departments,
            state="readonly",
        )
        dept_combo.grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(0, 10)
        )
        dept_combo.bind("<<ComboboxSelected>>", self.on_department_change)

        # Refresh button
        ttk.Button(main_frame, text="Refresh", command=self.populate_table).grid(
            row=0, column=2, padx=(10, 0), pady=(0, 10)
        )

        # Debug button to show unique categories
        ttk.Button(
            main_frame, text="Debug Categories", command=self.debug_categories
        ).grid(row=0, column=3, padx=(10, 0), pady=(0, 10))

        # Treeview for table
        columns = (
            "Case No",
            "Category",
            "Detail",
            "Problem Start",
            "Location",
            "Priority",
            "Score",
            "Status",
            "Caller",
            "Phone",
            "Latest Grievance",
        )
        self.tree = ttk.Treeview(
            main_frame, columns=columns, show="headings", height=20
        )

        # Configure column headings and widths
        column_widths = {
            "Case No": 80,
            "Category": 120,
            "Detail": 200,
            "Problem Start": 120,
            "Location": 120,
            "Priority": 70,
            "Score": 60,
            "Status": 80,
            "Caller": 120,
            "Phone": 120,
            "Latest Grievance": 200,
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            main_frame, orient="vertical", command=self.tree.yview
        )
        h_scrollbar = ttk.Scrollbar(
            main_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Grid layout for tree and scrollbars
        self.tree.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=1, column=3, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))

        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_item_double_click)

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.grid(
            row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0)
        )

        self.update_status()

    def debug_categories(self):
        """Debug function to show unique categories in the data"""
        unique_categories = set()
        for case in self.case_records:
            category = case.get("case_category", "")
            if category:
                unique_categories.add(category)

        message = "Unique categories found in data:\n\n"
        for cat in sorted(unique_categories):
            message += f"• {cat}\n"

        message += f"\nAvailable departments:\n\n"
        for dept in self.departments:
            message += f"• {dept}\n"

        messagebox.showinfo("Debug: Categories vs Departments", message)

    def categorize_case_by_keywords(self, case):
        """Categorize a case based on keywords matching"""
        case_text = (
            f"{case.get('case_category', '')} {case.get('case_detail', '')}"
        ).lower()

        best_match = None
        max_matches = 0

        for category in self.categories_data:
            if isinstance(category, dict) and "keywords" in category:
                matches = 0
                for keyword in category["keywords"]:
                    if keyword.lower() in case_text:
                        matches += 1

                if matches > max_matches:
                    max_matches = matches
                    best_match = category["name"]

        return best_match

    def on_department_change(self, event=None):
        """Handle department selection change"""
        self.current_department = self.dept_var.get()
        self.populate_table()
        self.update_status()

    def populate_table(self):
        """Populate the table with case records"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filter cases based on selected department
        filtered_cases = self.filter_cases_by_department()

        # Add filtered cases to tree
        for case in filtered_cases:
            # Get the latest grievance info
            caller_name = ""
            caller_phone = ""
            latest_grievance = ""

            thread = case.get("thread", [])
            if thread:
                # Parse datetime for sorting
                for grievance in thread:
                    date_str = grievance.get("date_time", "")
                    try:
                        # Try parsing different formats
                        if "T" in date_str:
                            parsed_date = datetime.fromisoformat(
                                date_str.replace("T", " ").replace("Z", "")
                            )
                        else:
                            parsed_date = datetime.strptime(
                                date_str, "%Y-%m-%d %H:%M:%S"
                            )
                        grievance["parsed_date"] = parsed_date
                    except:
                        grievance["parsed_date"] = datetime.min

                # Get latest grievance
                latest = max(thread, key=lambda g: g.get("parsed_date", datetime.min))
                caller_name = latest.get("caller_name", "")
                caller_phone = latest.get("caller_phone_no", "")
                description = latest.get("description", "")
                latest_grievance = (
                    description[:50] + "..." if len(description) > 50 else description
                )

            # Format case detail
            case_detail = case.get("case_detail", "")
            formatted_detail = (
                case_detail[:50] + "..." if len(case_detail) > 50 else case_detail
            )

            self.tree.insert(
                "",
                "end",
                values=(
                    case.get("case_no", ""),
                    case.get("case_category", ""),
                    formatted_detail,
                    case.get("problem_start", ""),
                    case.get("location", ""),
                    case.get("priority", ""),
                    case.get("score", 0),
                    case.get("status", ""),
                    caller_name,
                    caller_phone,
                    latest_grievance,
                ),
            )

    def filter_cases_by_department(self):
        """Filter cases based on selected department"""
        if self.current_department == "All Departments":
            return self.case_records

        filtered_cases = []
        for case in self.case_records:
            case_category = case.get("case_category", "")

            # Method 1: Direct string matching
            if case_category == self.current_department:
                filtered_cases.append(case)
                continue

            # Method 2: Keyword-based matching
            if self.categories_data:
                predicted_dept = self.categorize_case_by_keywords(case)
                if predicted_dept == self.current_department:
                    filtered_cases.append(case)
                    continue

            # Method 3: Partial string matching (case insensitive)
            if (
                self.current_department.lower() in case_category["name"].lower()
                or case_category["name"].lower() in self.current_department.lower()
            ):
                filtered_cases.append(case)

        return filtered_cases

    def on_item_double_click(self, event):
        """Handle double-click on table item"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            case_no = item["values"][0]

            # Find the case record
            case = next(
                (c for c in self.case_records if c.get("case_no") == case_no), None
            )
            if case:
                self.show_case_details(case)

    def show_case_details(self, case):
        """Show detailed information about a case"""
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Case Details - {case.get('case_no', '')}")
        detail_window.geometry("600x500")

        # Create notebook for tabs
        notebook = ttk.Notebook(detail_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Case Info tab
        case_frame = ttk.Frame(notebook)
        notebook.add(case_frame, text="Case Information")

        info_labels = [
            ("Case No:", case.get("case_no", "")),
            ("Category:", case.get("case_category", "")),
            ("Detail:", case.get("case_detail", "")),
            ("Problem Start:", case.get("problem_start", "")),
            ("Location:", case.get("location", "")),
            ("Priority:", str(case.get("priority", ""))),
            ("Score:", str(case.get("score", 0))),
            ("Status:", case.get("status", "")),
        ]

        for i, (label, value) in enumerate(info_labels):
            ttk.Label(case_frame, text=label, font=("Arial", 10, "bold")).grid(
                row=i, column=0, sticky=tk.W, padx=10, pady=5
            )
            ttk.Label(case_frame, text=value, wraplength=400).grid(
                row=i, column=1, sticky=tk.W, padx=10, pady=5
            )

        # Grievances tab
        thread = case.get("thread", [])
        grievances_frame = ttk.Frame(notebook)
        notebook.add(grievances_frame, text=f"Grievances ({len(thread)})")

        if thread:
            # Create treeview for grievances
            grv_columns = ("Date/Time", "Caller", "Phone", "Location", "Description")
            grv_tree = ttk.Treeview(
                grievances_frame, columns=grv_columns, show="headings"
            )

            for col in grv_columns:
                grv_tree.heading(col, text=col)
                grv_tree.column(col, width=100)

            # Sort grievances by date (newest first)
            sorted_thread = sorted(
                thread, key=lambda g: g.get("parsed_date", datetime.min), reverse=True
            )

            for grievance in sorted_thread:
                date_str = grievance.get("date_time", "")
                # Format datetime for display
                try:
                    if "T" in date_str:
                        dt = datetime.fromisoformat(
                            date_str.replace("T", " ").replace("Z", "")
                        )
                        formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                    else:
                        formatted_date = date_str
                except:
                    formatted_date = date_str

                description = grievance.get("description", "")
                formatted_desc = (
                    description[:100] + "..." if len(description) > 100 else description
                )

                grv_tree.insert(
                    "",
                    "end",
                    values=(
                        formatted_date,
                        grievance.get("caller_name", ""),
                        grievance.get("caller_phone_no", ""),
                        grievance.get("location", ""),
                        formatted_desc,
                    ),
                )

            grv_tree.pack(fill="both", expand=True, padx=10, pady=10)
        else:
            ttk.Label(
                grievances_frame, text="No grievances recorded for this case."
            ).pack(padx=10, pady=10)

    def update_status(self):
        """Update status bar"""
        filtered_count = len(self.filter_cases_by_department())
        total_count = len(self.case_records)

        if self.current_department == "All Departments":
            status_text = f"Showing {total_count} cases"
        else:
            status_text = f"Showing {filtered_count} cases in {self.current_department} (Total: {total_count})"

        self.status_var.set(status_text)


def main():
    root = tk.Tk()
    app = GrievanceManagementGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
