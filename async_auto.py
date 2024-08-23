import asyncio
from datetime import datetime, timedelta


# Placeholder API functions
async def get_master_number_from_api():
    # Simulate API request to get master number
    print("Getting master number from API...")
    await asyncio.sleep(1)  # Simulating network delay
    return "123456"  # Return a master number or empty string if no more to process


async def return_result_to_api(master_number, result):
    # Simulate API request to return result
    print(f"Returning result to API: Master Number {master_number}, Result {result}")
    await asyncio.sleep(1)  # Simulating network delay


# Check function for entries
async def check_master_number(master_number):
    # Simulate the checking process
    print(f"Checking master number {master_number}...")
    await asyncio.sleep(2)  # Simulating time taken to check
    return True  # Return True if check passes, False otherwise


# Task to periodically check entries in the previous checklist
async def periodic_checklist_task(previous_checklist, processed_set):
    while True:
        current_time = datetime.now()
        if current_time.minute == 0:  # Execute at the start of every hour
            print("Checking the previous hour's checklist...")
            for _ in range(len(previous_checklist)):
                master_number = previous_checklist.pop(0)
                result = await check_master_number(master_number)
                await return_result_to_api(master_number, "Pass" if result else "Fail")
                processed_set.remove(master_number)  # Remove from processed set after checking
            print("Checklist check complete!")
        await asyncio.sleep(60)  # Check every minute


# Task to handle processing of master numbers
async def handle_master_numbers(current_checklist, processed_set):
    while True:
        master_number = await get_master_number_from_api()
        if master_number:
            if master_number not in processed_set:
                print(f"Processing master number {master_number}...")
                try:
                    processed_set.add(master_number)  # Mark as being processed
                    await asyncio.sleep(3)  # Simulating processing time
                    current_checklist.append(master_number)  # Add to current checklist
                    print(f"Master number {master_number} processed and added to current checklist.")
                except Exception as e:
                    print(f"Error processing master number {master_number}: {e}")
                    await return_result_to_api(master_number, "Error")
                    processed_set.remove(master_number)  # Remove from set if processing fails
            else:
                print(f"Master number {master_number} already processed or in progress, skipping.")
        else:
            print("No master number to process, sleeping for 30 minutes...")
            await asyncio.sleep(1800)  # Sleep for 30 minutes


# Main function to run both tasks concurrently and manage checklist switching
async def main():
    current_checklist = []  # Checklist for the current hour
    previous_checklist = []  # Checklist for the previous hour
    processed_set = set()  # Set to track processed or in-progress master numbers

    task1 = asyncio.create_task(handle_master_numbers(current_checklist, processed_set))
    task2 = asyncio.create_task(periodic_checklist_task(previous_checklist, processed_set))

    start_time = datetime.now()  # Track the start time of the hour

    while True:
        await asyncio.sleep(60)  # Wait 60 seconds before checking time again
        current_time = datetime.now()

        # Check if an hour has passed since the start time
        if current_time - start_time >= timedelta(hours=1):
            print(f"Hour passed. Swapping checklists at {current_time.strftime('%H:%M:%S')}.")

            # Move current to previous and reset current
            previous_checklist.extend(current_checklist)
            current_checklist.clear()

            # Update start time to the current time
            start_time = current_time


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
