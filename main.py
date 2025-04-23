# Import required libraries
# Requests - to make API calls
# Datetime - to format timestamps into readable dates
# Tabulate - to format data into tables
# Colorama - to add color and styling to terminal outputs
import requests
from datetime import datetime
from tabulate import tabulate
from colorama import Fore, Style, Back, init
# Initialize Colorama for auto-reset after each print statement
init(autoreset=True)
import sys     # Provides system-related functions like exiting the program
import config  # Import the config file to access API keys

# Define API constants for OpenWeather API
API_KEY = config.API_KEY  # API key for authentication
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"  # Base URL for current weather
FORECAST_BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"  # Base URL for forecast API


# Function to update README.md dynamically with the latest app version
def update_readme():
    """
    Reads README.md, removes the previous version line, and prepends the latest version.
    This ensures the README file always reflects the most recent app version without stacking versions.
    """
    with open("README.md","r",encoding='utf-8') as file:
        file_content = file.readlines() # Read file content as a list of lines
        latest_version = grab_version() # Get the latest version from version.txt
    # rewrite the readme file with the version on top
    with open("README.md","w",encoding='utf-8') as file:
        file_content = file_content[1:] # Remove the first line (previous version entry)
        file_content = "".join(file_content) # Convert list back into a string
        file.write("# App Version: " + latest_version +"\n" + file_content) # Write updated version at the top


# Function to extract the latest version from version.txt
def grab_version():
    """
    Reads version.txt, identifies the most recent version number, and returns it.
    Skips empty lines and comments, ensuring only valid version entries are considered.
    """
    with open("version.txt","r") as file:
        lines = file.readlines() # Read file content line by line
    for line in reversed(lines):
        if line.strip() and not line.strip().startswith('#'): # Ignore empty lines and comments
            if "-" in line: # Expected format: 'version-number'
                latest_version = line.split("-")[0] # Extract the version number before '-'
                break
    return latest_version

# Helper function to calculate min and max temperatures from weather data
def grab_min_max_temp(weather_data):
    """
    Extract minimum and maximum temperatures from the weather data
    Convert from Kelvin to Fahrenheit for readability
    """
    min_temp_kalvin = weather_data['main']['temp_min']
    min_temp_actual = round((min_temp_kalvin - 273.15) * 9/5 + 32)  # Convert to Fahrenheit
    max_temp_kalvin = weather_data['main']['temp_max']
    max_temp_actual = round((max_temp_kalvin - 273.15) * 9/5 + 32)  # Convert to Fahrenheit
    return min_temp_actual, max_temp_actual

# Helper function to convert Unix timestamps into readable date strings
def convert_date_time(unix_timestamp):
    """
    Convert Unix timestamp to a human-readable format
    Example Output: 'Monday, June 08'
    """
    date_time_object = datetime.fromtimestamp(unix_timestamp)  # Convert timestamp to datetime
    friendly_date_conversion = date_time_object.strftime('%A, %B %d')  # Format datetime as string
    return friendly_date_conversion

# Function to fetch and display the three-day weather forecast
def get_three_day_forecast(city_name):
    """
    Fetch the 3-day weather forecast for the given city
    Display the forecast as a formatted table with colorful output
    """
    # Build the Forecast API URL and make the API call
    url = f"{FORECAST_BASE_URL}?q={city_name}&appid={API_KEY}"
    response = requests.get(url)  # Perform API call
    forecast_data = response.json()  # Parse JSON response into Python dictionary

    # Build the Current Weather API URL for additional data
    weather_url = f"{BASE_URL}?q={city_name}&appid={API_KEY}"
    weather_response = requests.get(weather_url)  # Perform API call
    weather_data = weather_response.json()  # Parse JSON response into Python dictionary

    # Handle API errors gracefully
    if forecast_data.get("cod") != "200":
        forecast_error_message = forecast_data.get("message", "Unknown error here")
        print(f"{Fore.RED}❌ Error: {forecast_error_message}")
        return

    # Prepare table rows for Tabulate
    table_data = []
    # Track unique days to ensure only three days are processed
    three_days_list = []

    # Iterate through the forecast data, grouping by date
    for entry_date in forecast_data['list']:
        date = entry_date['dt_txt'].split(" ")[0]  # Extract date (YYYY-MM-DD)
        if date in three_days_list:  # Skip if this date is already processed
            continue
        three_days_list.append(date)  # Add unique date to the list

        # Extract relevant weather data for this forecast interval
        forecast_date = entry_date['dt']
        forecast_city = forecast_data.get('city', {}).get('name', "Unknown City")  # Get city name
        forecast_country = forecast_data.get('city', {}).get('country', "Unknown Country")  # Get country code
        forecast_location = f"{forecast_city}, {forecast_country}"  # Combine city and country into one string

        min_temp_actual, max_temp_actual = grab_min_max_temp(weather_data)  # Fetch min and max temperatures
        weather_condition = entry_date['weather'][0]['description']  # Fetch weather condition
        precipitation = entry_date.get('pop', 0) * 100  # Fetch precipitation probability
        humidity = entry_date['main']['humidity']  # Fetch humidity percentage

        # Add row data to the table with colors and emojis
        table_data.append([
            f"{Fore.WHITE}📅 {convert_date_time(forecast_date)}",
            f"{Fore.CYAN}📍 {forecast_location}",                             
            f"{Fore.BLUE}🌡️  ↘️  {min_temp_actual}°F",
            f"{Fore.BLUE}🌡️  ↗️  {max_temp_actual}°F ",                               
            f"{Fore.WHITE}{weather_condition} ☁️ ",                            
            f"{Fore.BLUE}{precipitation:.1f}% 🌧️ ",                            
            f"{Fore.MAGENTA}{humidity}% 💧{Style.RESET_ALL}"                                   
        ])

        # Exit the loop after processing 3 unique days
        if len(three_days_list) == 3:
            break

    # Define table headers for Tabulate
    weather_headers = ["Date", "Location", "Min Temp", "Max Temp", "Condition", "Precipitation", "Humidity"]
    # Print the forecast table
    print(tabulate(table_data, headers=weather_headers, tablefmt="grid"))

# Function to fetch and display the current weather
def get_weather(city_name):
    """
    Fetch the current weather for the given city
    Display the weather data as a formatted table with colorful output
    """
    url = f"{BASE_URL}?q={city_name}&appid={API_KEY}"  # Build API URL
    response = requests.get(url)  # Perform API call
    weather_data = response.json()  # Parse JSON response into Python dictionary

    # Handle API errors gracefully
    if weather_data.get("cod") != 200:
        weather_error_message = weather_data.get("message", "Unknown error here")
        print(f"{Fore.RED}❌ Error: {weather_error_message}")
        return

    # Extract relevant weather data
    weather_date = weather_data['dt']  # Get the Unix timestamp for the current weather
    weather_location = weather_data['name']  # Get city name
    min_temp_actual, max_temp_actual = grab_min_max_temp(weather_data)  # Fetch min and max temperatures
    weather_condition = weather_data['weather'][0]['description']  # Fetch weather condition
    humidity = weather_data['main']['humidity']  # Fetch humidity percentage

    # Prepare table rows for Tabulate
    table_data = []

    # Add row data to the table with colors and emojis
    table_data.append([
        f"{Fore.WHITE}📅 {convert_date_time(weather_date)}",  
        f"{Fore.CYAN}📍 {weather_location}",
        f"{Fore.BLUE}🌡️  ↘️  {min_temp_actual}°F",
        f"{Fore.BLUE}🌡️  ↗️  {max_temp_actual}°F ",
        f"{Fore.WHITE}☁️  {weather_condition}",
        f"{Fore.CYAN}💧 {humidity}%{Style.RESET_ALL}",
    ])

    # Define table headers for Tabulate
    weather_headers = ["Date", "Location", "Min Temp", "Max Temp", "Condition", "Humidity"]
    # Print the weather table
    print(tabulate(table_data, headers=weather_headers, tablefmt="grid"))

# Main function to handle user interaction
def main():
    """
    Main program loop to interact with the user
    Allows the user to choose between current weather, 3-day forecast, or exit
    """
    #Update READM.md with APP version
    update_readme()
    #display version here
    print(f"App Version: {grab_version()}")
    while True:
        user_option = input(f"Hi! select an option:"
                            "\n 1: Current Weather"
                            "\n 2: Three day forecast"
                            "\n 3: Exit program"
                            "\n Option selected:")
        if user_option.isdigit():  # Ensure valid input
            user_option = int(user_option)
            if user_option == 1 or user_option == 2:
                user_city_selection = input("Enter City (or 'exit' to leave): ")
                if user_city_selection.lower() == "exit":
                    print("Goodbye, exiting weather checker!")
                    sys.exit()
                elif user_city_selection.strip() == "":  # Prevent empty city input
                    print("Sorry, input cannot be empty")
                    continue
                elif user_city_selection.replace(" ", "").isalpha():  # Validate alphabetic input
                    if user_option == 1:
                        get_weather(user_city_selection)
                    else:
                        get_three_day_forecast(user_city_selection)
                else:
                    print("Invalid input. Please enter a valid city name.")
            elif user_option == 3:  # Exit program
                print("Goodbye, exiting weather checker!")
                sys.exit()
            else:
                print("Invalid input. Please enter a valid option.")
        else:
            print("Invalid input. Please enter a number (1, 2, or 3).")

# Run the main program if the script is executed directly
if __name__ == "__main__":
    main()
