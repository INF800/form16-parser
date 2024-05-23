from pathlib import Path
from typing import Any

from loguru import logger
from form16_parser.pdf import PDF
from form16_parser._exceptions import UnsupportedForm16Error

    
class Parser:
    VALID_ROW_QUERIES_PARTB = {
        "Annexure - I",
        "Details of Salary Paid and any other income and tax deducted",
        "0-Details of Salary Paid and any other income and tax deducted", # Year 2019
        "Whether opting for taxation u/s 115BAC",
        "A", # FY2425 (For "Whether opting out of taxation u/s 115BAC(1A)?")
        "Whethe", # Honeywell Part B
        "__no", # Honeywell Part B
        "1.",
        "(a)",
        "(b)",
        "(c)",
        "(d)",
        "(e)",
        "2.",
        "(a)",
        "(b)",
        "(c)",
        "(d)",
        "(e)",
        "(f)",
        "(g)",
        "(h)",
        "3.",
        "4.",
        "(a)",
        "(b)",
        "(c)",
        "5.",
        "6.",
        "7.",
        "(a)",
        "(b)",
        "8.",
        "9.",
        "10.",
        "(a)",
        "(b)",
        "(c)",
        "(d)",
        "(e)",
        "0-(f)",
        "0-(h)", # FY2425
        "(g)",
        "(h)",
        "__grossamount__qualifyingamount__deductibleamount",
        "(i)",
        "(j)",
        "(k)",
        "(l)",
        "(m)", # FY2425
        "(n)", # FY2425
        "11.",
        "12.",
        "13.",
        "14.",
        "15.",
        "16.",
        "17.",
        "18.",
        "19.",
        "Verification",
        "I, ",
        "Place",
        "Date",
    }

    VALID_ROW_QUERIES_PARTA_SUMMARY = {
        "Q1", "Q2", "Q3", "Q4", "Total (Rs.)",
    }

    VALID_ROW_QUERIES_PARTA_SECTION1AND2 = {
        "I. DETAILS OF TAX DEDUCTED AND DEPOSITED IN THE CENTRAL GOVERNMENT ACCOUNT THROUGH BOOK ADJUSTMENT\n(The deductor to provide payment wise details of tax deducted and deposited with respect to the deductee)",
        "II. DETAILS OF TAX DEDUCTED AND DEPOSITED IN THE CENTRAL GOVERNMENT ACCOUNT THROUGH CHALLAN\n(The deductor to provide payment wise details of tax deducted and deposited with respect to the deductee)",   
        "Total (Rs.)",
        "Total",
    }

    VALID_ROW_QUERIES_PARTA_LEGEND = {
        "U", "P", "F", "O",
    }


    def __init__(self) -> None:
        pass

    @staticmethod
    def is_form16(pdf: PDF):
        try:
            first_cell = pdf.tables[0].first_table_cell
            if first_cell=="FORM NO. 16":
                return True
        except Exception as e:
            logger.error(f"Recovering from error: {e}")
            return False
        return False
        
    @staticmethod
    def parts_info(pdf, return_offset: bool = False):
        first_columns = pdf.first_table_columns
        offsets_a = []
        offsets_b = []
        for tid, first_column in enumerate(first_columns):
            for rid, cell in enumerate(first_column):
                if cell == "PART A":
                    offsets_a.append((tid, rid))
                elif cell == "PART B":
                    offsets_b.append((tid, rid))
        
        assert len(offsets_a)<=1, "Multiple PART-A headings found!"
        assert len(offsets_b)<=1, "Multiple PART-B headings found!"

        part_a_available = bool(offsets_a)
        part_b_available = bool(offsets_b)

        assert part_a_available or part_b_available, "Either PART A or PART B must be present in the form."

        ret_offsets_a = {
            "table_index": offsets_a[0][0] if part_a_available else -1,
            "row_index": offsets_a[0][1] if part_a_available else -1,
        } if return_offset else {}
        
        ret_offsets_b = {
            "table_index": offsets_b[0][0]  if part_b_available else -1,
            "row_index": offsets_b[0][1]  if part_b_available else -1,
        } if return_offset else {}
        
        return {
            "part_a": {
                "available": part_a_available,
                **ret_offsets_a,
            },
            "part_b": {
                "available": part_b_available,
                **ret_offsets_b,
            },
        }


    @staticmethod
    def is_valid_part_a_sec_row(row):
        def _validate(row):
            query = row[1]
            if query in Parser.VALID_ROW_QUERIES_PARTA_SECTION1AND2:
                return True
            try:
                _ = int(query)
                return True
            except:
                return False
                
        if _validate(row):
            return True
        return False
    
    def is_valid_part_a_legend_row(row):
        query = row[1]
        if query in Parser.VALID_ROW_QUERIES_PARTA_LEGEND:
            return True
        return False

    def parse_a(self, tables):
        info = {}
        first_table = tables[0]

        # Extract the general details
        row4 = [c for c in first_table.dataframe.iloc[4].to_list() if c is not None]
        row6 = [c for c in first_table.dataframe.iloc[6].to_list() if c is not None]
        row8 = [c for c in first_table.dataframe.iloc[8].to_list() if c is not None]
        row10 = [c for c in first_table.dataframe.iloc[10].to_list() if c is not None]

        info["certificate_num"] = row4[1].replace("Certificate No. ", "")
        info["last_updated"] = row4[2].replace("Last updated on ", "")
        info["name_and_address_of_the_employer_or_specified_bank"] = row6[1] 
        info["name_and_address_of_the_employee_or_specified_senior_citizen"] = row6[2]
        info["pan_of_the_deductor"] = row8[1]
        info["tan_of_the_deductor"] = row8[2]
        info["pan_of_the_employee_or_specified_senior_citizen"] = row8[3]
        info["employee_ref_num_or_ppo_num_provided_by_employer"] = row8[4]
        info["cit_tds"] = row10[1]
        info["assesment_year"] = row10[2]
        info["period_with_the_employer_from"] = row10[3].replace("From\n", "")
        info["period_with_the_employer_to"] = row10[4].replace("To\n", "")

        # Extract: Summary of amount paid/credited and tax deducted at source thereon in respect of the employee
        row11 = [c for c in first_table.dataframe.iloc[11].to_list() if c is not None]
        assert "Summary of amount paid/credited and tax deducted at source thereon in respect of the employee" == row11[1]

        info["summary_of_amount_paid_or_credited_and_tax_deducted"] = {}
        qidx = 13
        # Fix: Honeywell Form 16
        if len(tables[0].dataframe)<13:
            first_table = tables[1]
            qidx = 1
        qrow = [c for c in first_table.dataframe.iloc[qidx].to_list() if c is not None]
        qn = int(qrow[1][1:]) if (len(qrow[1])==2 and qrow[1][0]=="Q") else 1
        while qrow[1]==f"Q{qn}":
            info["summary_of_amount_paid_or_credited_and_tax_deducted"][f"q{qn}"] = {
                "recieit_number": qrow[2],
                "amt_paid_or_credited": qrow[3],
                "amt_of_tax_deducted": qrow[4],
                "amt_of_tax_deposited_or_remitted": qrow[5],
            }
            qn+=1
            qidx+=1
            qrow = [c for c in first_table.dataframe.iloc[qidx].to_list() if c is not None]

        total = [c for c in first_table.dataframe.iloc[qidx].to_list() if c is not None]
        info["summary_of_amount_paid_or_credited_and_tax_deducted"]["total"] = {
            "total_amt_paid_or_credited": total[3],
            "total_amt_of_tax_deducted": total[4],
            "total_amt_of_tax_deposited_or_remitted": total[5],
        }

        # Extract: I. DETAILS OF TAX DEDUCTED AND DEPOSITED IN THE CENTRAL GOVERNMENT ACCOUNT THROUGH BOOK ADJUSTMENT
        # Note: we cannot use main table / static indices from here
        qidx+=1
        hrow = [c for c in first_table.dataframe.iloc[qidx].to_list() if c is not None]
        forma_sec1_header = (
            "I. DETAILS OF TAX DEDUCTED AND DEPOSITED IN THE CENTRAL GOVERNMENT ACCOUNT THROUGH BOOK ADJUSTMENT\n"
            "(The deductor to provide payment wise details of tax deducted and deposited with respect to the deductee)"
        )
        assert forma_sec1_header == hrow[1], f"{hrow[1]}"

        # flatten the tables and collect
        all_rows = []
        ridx = qidx
        while ridx<len(first_table.dataframe):
            row = first_table.dataframe.iloc[ridx]
            all_rows.append([c for c in row.to_list() if c is not None])
            ridx+=1

        table_beg = 1

        # Fix: Honeywell Form 16
        if len(tables[0].dataframe)<13:
            table_beg = 2

        for table in tables[table_beg:]:
            ridx = 0
            while ridx<len(table.dataframe):
                row = table.dataframe.iloc[ridx]
                all_rows.append([c for c in row.to_list() if c is not None])
                ridx+=1

        # Find the table borders
        forma_sec2_header = (
            "II. DETAILS OF TAX DEDUCTED AND DEPOSITED IN THE CENTRAL GOVERNMENT ACCOUNT THROUGH CHALLAN\n"
            "(The deductor to provide payment wise details of tax deducted and deposited with respect to the deductee)"
        )
        forma_verification_header = "Verification"
        forma_legend_header = "Legend"
        forma_sec1_beg_idxs = []
        forma_sec2_beg_idxs = []
        forma_verification_beg_idxs = []
        forma_legend_beg_idxs = []
        for i, row in enumerate(all_rows):
            if row[1] == forma_sec1_header:
                forma_sec1_beg_idxs.append(i)
            if row[1] == forma_sec2_header:
                forma_sec2_beg_idxs.append(i)
            if row[1] == forma_verification_header:
                forma_verification_beg_idxs.append(i)
            if row[1] == forma_legend_header:
                forma_legend_beg_idxs.append(i)

        if len(forma_sec1_beg_idxs)==1:
            logger.warning(
                "There must be only one main heading for Form A Section 1. "
                "Make sure your PDF file is an un-modified Form16. "
                "Parsed output might be incorrect.")
        if len(forma_sec2_beg_idxs)==1:
            logger.warning(
                "There must be only one main heading for Form A Section 2. "
                "Make sure your PDF file is an un-modified Form16. "
                "Parsed output might be incorrect.")
        if len(forma_verification_beg_idxs)==1:
            logger.warning(
                "There must be only one main heading for Form A Verification. "
                "Make sure your PDF file is an un-modified Form16. "
                "Parsed output might be incorrect.")
        if len(forma_legend_beg_idxs)>=1:
            logger.warning(
                "There must be legend available in the form for Legend. "
                "Make sure your PDF file is an un-modified Form16. "
                "Parsed output might be incorrect.")

        # parse the tables
        sec1_rows = all_rows[forma_sec1_beg_idxs[0]:forma_sec2_beg_idxs[0]]
        sec2_rows = all_rows[forma_sec2_beg_idxs[0]:forma_verification_beg_idxs[0]]
        verf_rows = all_rows[forma_verification_beg_idxs[0]:forma_legend_beg_idxs[0]]
        lgnd_rows = all_rows[forma_legend_beg_idxs[0]:]

        # remove the redundant headers
        sec1_rows = [row for row in sec1_rows if row[1] not in ("Sl. No.", "Receipt Numbers of Form\nNo. 24G")]
        sec2_rows = [row for row in sec2_rows if row[1] not in ("Sl. No.", "BSR Code of the Bank\nBranch")]
        lgnd_rows = [row for row in lgnd_rows if row[1]!="Legend"]

        # remove invalid rows
        sec1_rows = [row for row in sec1_rows if Parser.is_valid_part_a_sec_row(row)]
        sec2_rows = [row for row in sec2_rows if Parser.is_valid_part_a_sec_row(row)]
        lgnd_rows = [row for row in lgnd_rows if Parser.is_valid_part_a_legend_row(row)]

        # collect form a section 1 
        info["section_1_tax_deducted_and_deposited_through_book_adjustment"] = []
        for row in sec1_rows[1:-1]:
            info["section_1_tax_deducted_and_deposited_through_book_adjustment"].append({
                "serial_num": row[1],
                "tax_deposited_in_respect_of_the_deductee": row[2],
                "reciept_nums_of_form_num_24g": row[3],
                "ddo_serial_number_in_form_num_24g": row[4],
                "date_of_transfer_voucher": row[5],
                "status_of_matching_with_form_num_24g": row[6]
            })
        
        info["section_1_tax_deducted_and_deposited_through_book_adjustment"].append({
            "total": sec1_rows[-1][2]
        })

        # collect form a section 2
        info["section_2_tax_deducted_and_deposited_through_challan"] = []
        for row in sec2_rows[1:-1]:
            info["section_2_tax_deducted_and_deposited_through_challan"].append({
                "serial_num": row[1],
                "tax_deposited_in_respect_of_the_deductee": row[2],
                "bsr_code_of_the_bank_branch": row[3],
                "date_on_which_tax_deposited": row[4],
                "challan_serial_num": row[5],
                "status_of_matching_with_oltas*": row[6],
            })

        info["section_2_tax_deducted_and_deposited_through_challan"].append({
            "total": sec2_rows[-1][2]
        })

        # collect verification
        info["verification"] = {
            "verification_text": verf_rows[1][1],
            "place": verf_rows[2][2],
            "date": verf_rows[3][2],
            "designation": verf_rows[4][1].replace("Designation:", ""),
            "full_name": verf_rows[4][2].replace("Full Name:", "",)
        }

        # collect legend
        info["legend_used_in_form_16"] = []
        for row in lgnd_rows:
            info["legend_used_in_form_16"].append({
                "legend": row[1],
                "description": row[2],
                "definition": row[3],
            })

        return info
    

    @staticmethod
    def table_typle(table):
        # TODO: Refactor the code
        first_row = table.first_table_row
        if len(first_row)>=2 and first_row[1]=="FORM NO. 16":
            return "MAIN"
        elif len(first_row)>=6 and first_row[5]=="Book Identification Number (BIN)":
            return "PARTA_SECTION1"
        elif len(first_row)>=6 and first_row[5]=="Challan Identification Number (CIN)":
            return "PARTA_SECTION2"
        elif len(first_row)>=2 and first_row[1]=="Legend":
            return "PARTA_LEGEND"
        elif len(first_row)>=2 and first_row[1]=="Annexure - I":
            return "PARTB_ANNEXURE1_0"
        elif len(first_row)>=2 and first_row[1]=="Details of Salary Paid and any other income and tax deducted":
            return "PARTB_ANNEXURE1_0_FY2122"
        elif len(first_row)>=2 and first_row[1]=="0-Details of Salary Paid and any other income and tax deducted":
            return "PARTB_ANNEXURE1_0_FY1920_FY2021"
        elif len(first_row)>=2 and first_row[1]=="(f)":
            return "PARTB_ANNEXURE1_1"
        elif len(first_row)>=2 and first_row[1]=="(g)":
            return "PARTB_ANNEXURE1_1_FY2425"
        elif len(first_row)>=2 and first_row[1]=="0-(f)":
            return "PARTB_ANNEXURE1_2"
        elif len(first_row)>=2 and first_row[1]=="0-(h)":
            return "PARTB_ANNEXURE1_2_FY2425"
        elif len(first_row)>=2 and first_row[1]=="2. (f) Break up for ‘Amount of any other exemption under section 10’ to be filled in the table below":
            return "PARTB_SECTION10_2F" # Note: Not processing these tables
        elif len(first_row)>=2 and first_row[1]=="10(k). Break up for ‘Amount deductible under any other provision(s) of Chapter VIA ‘to be filled in the table below":
            return "PARTB_CHAPTERVIA_10K"  # Note: Not processing these tables and the tables below it.
        else:
            return "UNKNOWN"
        
    @staticmethod
    def is_valid_table(table_type):
        if table_type in (
            "MAIN",
            "PARTA_SECTION1",
            "PARTA_SECTION2",
            "PARTA_LEGEND",
            "PARTB_ANNEXURE1_0",
            "PARTB_ANNEXURE1_0_FY2122",
            "PARTB_ANNEXURE1_0_FY1920_FY2021",
            "PARTB_ANNEXURE1_1",
            "PARTB_ANNEXURE1_1_FY2425",
            "PARTB_ANNEXURE1_2",
            "PARTB_ANNEXURE1_2_FY2425",
        ):
            return True
        return False

    @staticmethod
    def is_valid_part_b_row(row):
        # build query
        query = row[1]
        if query is None:
            query = row[2]
        if len(query)>100:
            query = query[:3]
        if query=="":
            query = "__".join([str(c).lower().replace("\n", "").replace(" ", "") for c in row[1:] if c is not None])

        # validate query
        if query in Parser.VALID_ROW_QUERIES_PARTB:
            return True
        return False


    def parse_b(self, tables):
        info = {}
        first_table = tables[0]

        # Validate if Part B is official
        try:
            row3 = [c for c in first_table.dataframe.iloc[3].to_list() if c is not None]
            if "Certificate No." not in row3[1]:
                logger.warning("The input form 16 does not contain valid Part B... Skipping Part B.")
                return {}
        except:
            logger.warning("The input form 16 does not contain valid Part B... Skipping Part B.")
            return {}

        # Extract the general details
        row3 = [c for c in first_table.dataframe.iloc[3].to_list() if c is not None]
        row5 = [c for c in first_table.dataframe.iloc[5].to_list() if c is not None]
        row7 = [c for c in first_table.dataframe.iloc[7].to_list() if c is not None]
        row9 = [c for c in first_table.dataframe.iloc[9].to_list() if c is not None]

        info["certificate_num"] = row3[1].replace("Certificate No. ", "")
        info["last_updated"] = row3[2].replace("Last updated on ", "")
        info["name_and_address_of_the_employer_or_specified_bank"] = row5[1] 
        info["name_and_address_of_the_employee_or_specified_senior_citizen"] = row5[2]
        info["pan_of_the_deductor"] = row7[1]
        info["tan_of_the_deductor"] = row7[2]
        info["pan_of_the_employee_or_specified_senior_citizen"] = row7[3]
        info["cit_tds"] = row9[1]
        info["assesment_year"] = row9[2]
        info["period_with_the_employer_from"] = row9[3].replace("From\n", "")
        info["period_with_the_employer_to"] = row9[4].replace("To\n", "")

        # flatten the tables
        all_rows = []
        replace_rows_2_and_1 = False
        gather_extra_rows = False
        for table in tables[1:]:
            table_type = Parser.table_typle(table)
            is_valid_table = Parser.is_valid_table(table_type)
            if not is_valid_table:
                logger.debug(f"skipping table with first row: {table.first_table_row}")
                continue
            
            # Fix(2021): Annexure row is not present 
            # so add it to handle index errors
            if table_type == "PARTB_ANNEXURE1_0_FY2122":
                all_rows.append(["custom",])

            # Fix(2019): Annexure row and 115BAC rows are not present 
            # so add them to handle index errors
            if table_type == "PARTB_ANNEXURE1_0_FY1920_FY2021":
                all_rows.append(["custom"])
                all_rows.append(["custom", "Whether opting for taxation u/s 115BAC", "Not Available"])
                replace_rows_2_and_1 = True
                raise UnsupportedForm16Error(
                    "At this point in time, we do not support form 16s older than FY2122. "
                    "But stay tuned, future releases will definitely work for them! "
                    "You can remove this execption manually and parse them anyway."
                )

            # Fix(FY2425): Manage extra columns
            if table_type in ("PARTB_ANNEXURE1_1_FY2425", "PARTB_ANNEXURE1_2_FY2425"):
                gather_extra_rows = True

            ridx = 0
            while ridx<len(table.dataframe):
                row = table.dataframe.iloc[ridx].to_list()
                row_ = []
                if not Parser.is_valid_part_b_row(row):
                    ridx+=1
                    continue
                for cell in row:
                    if cell is not None:
                        if not ((len(str(cell)) in (4, 5)) and (str(cell).startswith("Col"))):
                            row_.append(cell)
                        else:
                            row_.append("")
                all_rows.append(row_)
                ridx+=1

        # Fix: replace the empty headers
        all_rows[36] = [c for c in all_rows[36] if c != ""]

        # Fix: Honeywell Part B
        if all_rows[3][1]=="Whethe":
            all_rows[3] = [
                "custom", "Whether opting for taxation u/s 115BAC", all_rows[2][2],
            ]
            all_rows.pop(2)

        # Fix(2019): replace row 2 with 1
        if replace_rows_2_and_1:
            all_rows[2], all_rows[1] = all_rows[1], all_rows[2]

        # Fix(FY2425): Manage extra columns
        spl_allowances_sec10_14_fy2425 = {}
        chapter_vi_a_fy2425 = {}
        if gather_extra_rows:
            spl_allowances_sec10_14_fy2425 = {
                "other_special_allowances_under_section_10_14": [
                    all_rows[15][3], 
                    all_rows[15][4],
                ]
            }
            chapter_vi_a_fy2425 = {
                "deduction_in_respect_of_contribution_by_employee_to_agnipath_scheme_under_section_80cch": [
                    all_rows[39][3],
                    all_rows[39][4],
                ],
                "deduction_in_respect_of_contribution_by_central_gov_to_agnipath_scheme_under_section_80cch": [
                    all_rows[40][3],
                    all_rows[40][4],
                ],
            }
            # Note: pop shifts the indices
            # We intend to pop original indices - 15, 39 and 40
            all_rows.pop(15)
            all_rows.pop(39) 
            all_rows.pop(39) 
            
            # Fix(FY2425): replace the empty headers
            all_rows[38] = [c for c in all_rows[38] if c != ""]

            # Fix(FY2425): whether_opting_for_taxation_us_115bac
            all_rows[2][2] = all_rows[2][3]

        # Fix(FY2425): Overalp issue with specific forms
        if all_rows[3][2] == "Whether opting out of taxation u/s 115BAC(1A)?":
            all_rows[2][2] = all_rows[2][3] # [1, 'A', '', 'No'] -> [1, 'A', 'No', 'No']

        # collect all values (all the row indices are static)
        info["details_of_salary_paid_and_any_other_income_and_tax_deducted"] = {
            "whether_opting_for_taxation_us_115bac": all_rows[2][2],
            "gross_salary": {
                "salary_as_per_provisions_contained_in_section_17_1": [
                    all_rows[4][3],
                    all_rows[4][4],
                ],
                "value_of_perquisites_under_section_17_2": [
                    all_rows[5][3],
                    all_rows[5][4],
                ],
                "profits_in_lieu_of_salary_under_section_17_3":[
                    all_rows[6][3],
                    all_rows[6][4],
                ],
                "total": all_rows[7][3],
                "reported_total_amount_of_salary_received_from_other_employers": [
                    all_rows[8][3],
                    all_rows[8][4],
                ]
            },
            "less_allowances_to_the_extent_exempt_under_section_10": {
                "travel_concession_or_assistance_under_section_10_5": [
                    all_rows[10][3],
                    all_rows[10][4],
                ],
                "death_cum_retirement_gratuity_under_section_10_10": [
                    all_rows[11][3],
                    all_rows[11][4],
                ],
                "commuted_value_of_pension_under_section_10_10A": [
                    all_rows[12][3],
                    all_rows[12][4],
                ],
                "cash_equivalent_of_leave_salary_encashment_under_section_10_10AA": [
                    all_rows[13][3],
                    all_rows[13][4],
                ],
                "house_rent_allowance_under_section_10_13A": [
                    all_rows[14][3],
                    all_rows[14][4],
                ],
                **spl_allowances_sec10_14_fy2425,
                "amount_of_any_other_exemption_under_section_10": [
                    all_rows[15][3],
                    all_rows[15][4],
                ],
                "total_amount_of_any_other_exemption_under_section_10": [
                    all_rows[16][3],
                    all_rows[16][4],
                ],
                "total_amount_of_exemption_claimed_under_section_10": [
                    all_rows[17][3],
                    all_rows[17][4],
                ],
            },
            "total_amount_of_salary_received_from_current_employer_1d_2h": [
                all_rows[18][3],
                all_rows[18][4],
            ],
            "less_deductions_under_section_16": {
                "standard_deduction_under_section_16_ia": [
                    all_rows[20][3],
                    all_rows[20][4],
                ],
                "entertainment_allowance_under_section_16_ii": [
                    all_rows[21][3],
                    all_rows[21][4],
                ],
                "tax_on_employment_under_section_16_iii": [
                    all_rows[22][3],
                    all_rows[22][4],  
                ],
            },
            "total_amount_of_deductions_under_section_16": [
                all_rows[23][3],
                all_rows[23][4],  
            ],
            "income_chargeable_under_the_head_salaries": [
                all_rows[24][3],
                all_rows[24][4],  
            ],
            "add_any_other_income_reported_by_the_employee_under_as_per_section_192_2b": {
                "income_or_admissible_loss_from_house_property_reported_by_employee_offered_for_tds": [
                    all_rows[26][3],
                    all_rows[26][4],  
                ],
                "income_under_the_head_other_sources_offered_for_tds": [
                    all_rows[27][3],
                    all_rows[27][4],  
                ],
            },
            "total_amount_of_other_income_reported_by_the_employee": [
                all_rows[28][3],
                all_rows[28][4],  
            ],
            "gross_total_income": [
                all_rows[29][3],
                all_rows[29][4],  
            ],
            "deductions_under_chapter_vi_a": {
                "deduction_in_respect_of_life_insurance_premia_pf_etc_under_section_80c": {
                    "gross_amount": all_rows[31][3],
                    "deductible_amount": all_rows[31][4],
                },
                "deduction_in_respect_of_contribution_to_certain_pension_funds_under_section_80ccc": {
                    "gross_amount": all_rows[32][3],
                    "deductible_amount": all_rows[32][4],
                },
                "deduction_in_respect_of_contribution_by_taxpayer_to_pensionscheme_under_section_80ccd_1": {
                    "gross_amount": all_rows[33][3],
                    "deductible_amount": all_rows[33][4],
                },
                "total_deduction_under_section_80c_80ccc_and_80ccd_1": {
                    "gross_amount": all_rows[34][3],
                    "deductible_amount": all_rows[34][4],
                },
                "deductions_in_respect_of_amount_paid_or_deposited_to_notified_pension_scheme_under_section_80ccd_1b": {
                    "gross_amount": all_rows[35][3],
                    "deductible_amount": all_rows[35][4],
                },
                "deduction_in_respect_of_contribution_by_employer_to_pension_scheme_under_section_80ccd_2": {
                    "gross_amount": all_rows[36][3].split("-")[1] if ("-" in all_rows[36][3]) else all_rows[36][3],
                    "deductible_amount": all_rows[36][4].split("-")[1] if ("-" in all_rows[36][4]) else all_rows[36][4],
                },
                "deduction_in_respect_of_health_insurance_premia_under_section_80d": {
                    "gross_amount": all_rows[37][3],
                    "deductible_amount": all_rows[37][4],
                },
                "deduction_in_respect_of_interest_on_loan_taken_for_higher_education_under_section_80e": {
                    "gross_amount": all_rows[38][3].split("-")[1] if ("-" in all_rows[38][3]) else all_rows[38][3],
                    "deductible_amount": all_rows[38][4].split("-")[1] if ("-" in all_rows[38][4]) else all_rows[38][4],
                },
                **chapter_vi_a_fy2425,
                "total_deduction_in_respect_of_donations_to_certain_funds_charitable_institutions_etc_under_section_80g": {
                    "gross_amount": all_rows[40][3],
                    "qualifying_amount": all_rows[40][4],
                    "deductible_amount": all_rows[40][5],
                },
                "deduction_in_respect_of_interest_on_deposits_in_savings_account_under_section_80tta": {
                    "gross_amount": all_rows[41][3],
                    "qualifying_amount": all_rows[41][4],
                    "deductible_amount": all_rows[41][5],
                },
                "amount_deductible_under_any_other_provisions_of_chapter_vi_a": all_rows[42][3],
                "total_amount_deductible_under_any_other_provisions_of_chapter_vi_a": {
                    "gross_amount": all_rows[43][3],
                    "qualifying_amount": all_rows[43][4],
                    "deductible_amount": all_rows[43][5],
                },
            },
            "aggregate_of_deductible_amount_under_chapter_vi_A": all_rows[44][3],
            "total_taxable_income": all_rows[45][3],
            "tax_on_total_income": all_rows[46][3],
            "rebate_under_section_87a_if_applicable": all_rows[47][3],
            "surcharge_wherever_applicable": all_rows[48][3],
            "health_and_education_cess": all_rows[49][3],
            "tax_payable": all_rows[50][3],
            "less_relief_under_section_89 ": all_rows[51][3],
            "net_tax_payable": all_rows[52][3],
        }

        info["verification"] = {
            "verification_text": all_rows[54][1],
            "place": all_rows[55][2],
            "date": all_rows[56][2],
            "full_name": all_rows[56][4],
        }

        return info


    def parse(self, filepath: str | Path, return_output: bool = False) -> None | dict:
        pdf = PDF(filepath)
        if not Parser.is_form16(pdf):
            raise Exception("Input is not an official PDF file of form 16. ")
        
        parts = Parser.parts_info(pdf, return_offset=True)
        if parts["part_a"]["available"] and parts["part_b"]["available"]:
            if parts["part_a"]["table_index"]>parts["part_b"]["table_index"]:
                logger.warning("Part B is present before Part A")
                atidx = parts["part_a"]["table_index"]
                part_b_tables = pdf.tables[:atidx]
                part_a_tables = pdf.tables[atidx:]
            else:
                btidx = parts["part_b"]["table_index"]
                part_a_tables = pdf.tables[:btidx]
                part_b_tables = pdf.tables[btidx:]

            a_info = self.parse_a(part_a_tables)
            b_info = self.parse_b(part_b_tables)
            pdf.clear()

            return {
                "part_a": a_info,
                "part_b": b_info,
            }
        
        elif parts["part_a"]["available"] and not parts["part_b"]["available"]:
            a_info = self.parse_a(pdf.tables)
            pdf.clear()
            return {
                "part_a": a_info,
            }
        
        elif not parts["part_a"]["available"] and parts["part_b"]["available"]:
            b_info = self.parse_b(pdf.tables)
            pdf.clear()
            return {
                "part_b": b_info,
            }
        
        else:
            raise Exception("Either PART A or PART B must be present in the form.")
            



def build_parser():
    p = Parser()
    return p