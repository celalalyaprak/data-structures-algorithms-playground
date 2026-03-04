# Validation script for age calculation in MS2
# Tests the age computation logic for Adding Information
# Author: Roman Harnastaeu

import csv
from project import _parse_birth_year, compute_age, build_athlete_index, build_games_index, read_csv_file


def test_birth_year_parsing():
    """Test the _parse_birth_year function with various formats"""
    print("="*70)
    print("Testing Birth Year Parsing (_parse_birth_year)")
    print("="*70)
    
    test_cases = [
        # (input, expected_output, description)
        ("04-Apr-49", 1949, "Legacy format - 1949"),
        ("15-Jan-00", 2000, "Legacy format - 2000"),
        ("20-Dec-24", 2024, "Legacy format - 2024"),
        ("25-Mar-98", 1998, "Legacy format - 1998"),
        ("2000-01-25", 2000, "Paris format - YYYY-MM-DD"),
        ("1995-06-15", 1995, "Paris format - 1995"),
        ("2024-08-01", 2024, "Paris format - 2024"),
        ("", None, "Empty string"),
        ("NA", None, "NA value"),
        ("UNKNOWN", None, "UNKNOWN value"),
        ("invalid", None, "Invalid format"),
    ]
    
    passed = 0
    failed = 0
    
    for input_val, expected, description in test_cases:
        result = _parse_birth_year(input_val)
        status = "PASS" if result == expected else "FAIL"
        
        if status == "PASS":
            passed += 1
            print(f"  {status}: {description}")
            print(f"        Input: '{input_val}' -> Output: {result}")
        else:
            failed += 1
            print(f"  {status}: {description}")
            print(f"        Input: '{input_val}'")
            print(f"        Expected: {expected}, Got: {result}")
        print()
    
    print(f"Summary: {passed} passed, {failed} failed")
    print()
    return passed, failed


def test_age_computation():
    """Test the compute_age function"""
    print("="*70)
    print("Testing Age Computation (compute_age)")
    print("="*70)
    
    test_cases = [
        # (birth_date, games_year, expected_age, description)
        ("2000-01-25", "2024", "24", "Paris format - 24 years old"),
        ("04-Apr-49", "1972", "23", "Legacy format - 23 years old"),
        ("15-Jan-00", "2024", "24", "Legacy format Y2K - 24 years old"),
        ("1990-05-15", "2024", "34", "Paris format - 34 years old"),
        ("", "2024", "UNKNOWN", "Empty birth date"),
        ("2000-01-25", "", "UNKNOWN", "Empty games year"),
        ("2025-01-01", "2024", "UNKNOWN", "Future birth date (negative age)"),
        ("1850-01-01", "2024", "UNKNOWN", "Age > 120"),
    ]
    
    passed = 0
    failed = 0
    
    for birth_date, games_year, expected, description in test_cases:
        result = compute_age(birth_date, games_year)
        status = "PASS" if result == expected else "FAIL"
        
        if status == "PASS":
            passed += 1
            print(f"  {status}: {description}")
            print(f"        Birth: '{birth_date}', Year: '{games_year}' -> Age: {result}")
        else:
            failed += 1
            print(f"  {status}: {description}")
            print(f"        Birth: '{birth_date}', Year: '{games_year}'")
            print(f"        Expected: {expected}, Got: {result}")
        print()
    
    print(f"Summary: {passed} passed, {failed} failed")
    print()
    return passed, failed


def verify_output_age_column():
    """Verify that the output file has age column and sample some values"""
    print("="*70)
    print("Verifying Age Column in Output File")
    print("="*70)
    
    try:
        # Read the output file
        results_data = read_csv_file("new_olympic_athlete_event_results.csv")
        header = results_data[0]
        
        # Check if age column exists
        if "age" not in header:
            print("  FAIL: 'age' column not found in header!")
            return 0, 1
        
        age_idx = header.index("age")
        print(f"  PASS: 'age' column found at index {age_idx}")
        print()
        
        # Count age statistics
        total_rows = len(results_data) - 1  # Exclude header
        unknown_count = 0
        valid_ages = []
        
        for row in results_data[1:]:
            age_value = row[age_idx]
            if age_value == "UNKNOWN":
                unknown_count += 1
            elif age_value.isdigit():
                valid_ages.append(int(age_value))
        
        valid_count = len(valid_ages)
        
        print(f"  Total rows: {total_rows}")
        print(f"  Valid ages: {valid_count} ({valid_count/total_rows*100:.2f}%)")
        print(f"  UNKNOWN ages: {unknown_count} ({unknown_count/total_rows*100:.2f}%)")
        
        if valid_ages:
            print(f"  Age range: {min(valid_ages)} - {max(valid_ages)}")
            print(f"  Average age: {sum(valid_ages)/len(valid_ages):.1f}")
        
        print()
        
        # Show sample records with ages
        print("  Sample records with calculated ages:")
        print("  " + "-"*66)
        
        sample_count = 0
        for i, row in enumerate(results_data[1:11], 1):  # Show first 10 rows
            athlete_name_idx = header.index("athlete")
            edition_idx = header.index("edition")
            
            athlete_name = row[athlete_name_idx]
            edition = row[edition_idx]
            age = row[age_idx]
            
            print(f"    {i}. {athlete_name[:30]:<30} | {edition[:20]:<20} | Age: {age}")
            sample_count += 1
        
        print()
        return 1, 0
        
    except Exception as e:
        print(f"  FAIL: Error reading output file: {e}")
        return 0, 1


def verify_paris_data_integration():
    """Verify that Paris 2024 data has ages calculated"""
    print("="*70)
    print("Verifying Paris 2024 Data Integration")
    print("="*70)
    
    try:
        results_data = read_csv_file("new_olympic_athlete_event_results.csv")
        header = results_data[0]
        
        edition_idx = header.index("edition")
        age_idx = header.index("age")
        athlete_idx = header.index("athlete")
        
        paris_rows = []
        for row in results_data[1:]:
            if "2024" in row[edition_idx]:
                paris_rows.append(row)
        
        if not paris_rows:
            print("  WARNING: No Paris 2024 records found")
            return 0, 1
        
        print(f"  Found {len(paris_rows)} Paris 2024 records")
        
        paris_with_age = sum(1 for row in paris_rows if row[age_idx] != "UNKNOWN")
        paris_unknown = sum(1 for row in paris_rows if row[age_idx] == "UNKNOWN")
        
        print(f"  With valid age: {paris_with_age} ({paris_with_age/len(paris_rows)*100:.2f}%)")
        print(f"  With UNKNOWN age: {paris_unknown} ({paris_unknown/len(paris_rows)*100:.2f}%)")
        print()
        
        # Show sample Paris athletes
        print("  Sample Paris 2024 athletes with ages:")
        print("  " + "-"*66)
        
        for i, row in enumerate(paris_rows[:5], 1):
            athlete_name = row[athlete_idx]
            age = row[age_idx]
            print(f"    {i}. {athlete_name[:40]:<40} | Age: {age}")
        
        print()
        return 1, 0
        
    except Exception as e:
        print(f"  FAIL: Error verifying Paris data: {e}")
        return 0, 1


def main():
    """Run all validation tests"""
    print("\n")
    print("*"*70)
    print("*" + " "*68 + "*")
    print("*" + "  AGE CALCULATION VALIDATION REPORT".center(68) + "*")
    print("*" + "  Roman Harnastaeu - MS2 'Adding Information' Task".center(68) + "*")
    print("*" + " "*68 + "*")
    print("*"*70)
    print("\n")
    
    total_passed = 0
    total_failed = 0
    
    # Test 1: Birth year parsing
    p, f = test_birth_year_parsing()
    total_passed += p
    total_failed += f
    
    # Test 2: Age computation
    p, f = test_age_computation()
    total_passed += p
    total_failed += f
    
    # Test 3: Verify output file
    p, f = verify_output_age_column()
    total_passed += p
    total_failed += f
    
    # Test 4: Verify Paris integration
    p, f = verify_paris_data_integration()
    total_passed += p
    total_failed += f
    
    print("="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"  Total tests passed: {total_passed}")
    print(f"  Total tests failed: {total_failed}")
    print()
    
    if total_failed == 0:
        print("  *** ALL TESTS PASSED ***")
        print("  Age calculation implementation is working correctly!")
    else:
        print(f"  *** {total_failed} TEST(S) FAILED ***")
        print("  Please review the failures above.")
    
    print()
    print("="*70)
    print()


if __name__ == "__main__":
    main()

