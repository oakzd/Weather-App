# Use project venv when PATH points at a Python without dependencies (common on Windows Git Bash)
import sys
from pathlib import Path

_VENV_PYTHON = Path(__file__).resolve().parent / "weather_env" / "Scripts" / "python.exe"


def _reexec_with_venv_if_needed():
    if not _VENV_PYTHON.is_file():
        return
    try:
        import requests  # noqa: F401
    except ImportError:
        if Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
            import os
            os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON), *sys.argv])
        print(
            "Missing dependencies. Run:\n"
            f"  {_VENV_PYTHON} -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)


_reexec_with_venv_if_needed()

# Import required libraries
# Requests - to make API calls
# Datetime - to format timestamps into readable dates
# Tabulate - to format data into tables
# Colorama - to add color and styling to terminal outputs
import requests
from collections import defaultdict
from datetime import datetime
from urllib.parse import quote
from tabulate import tabulate
from colorama import Fore, Style, Back, init
# Initialize Colorama for auto-reset after each print statement
init(autoreset=True)
import config  # Import the config file to access API keys

# Define API constants for OpenWeather API
API_KEY = config.API_KEY  # API key for authentication
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"  # Base URL for current weather
FORECAST_BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"  # Base URL for forecast API
REQUEST_TIMEOUT = 10  # Seconds before API requests time out


def kelvin_to_fahrenheit(kelvin):
    """Convert Kelvin to rounded Fahrenheit."""
    return round((kelvin - 273.15) * 9 / 5 + 32)


def _build_url(base, city):
    """Build an OpenWeather API URL with an encoded city name."""
    return f"{base}?q={quote(city.strip())}&appid={API_KEY}"


def _fetch_json(url):
    """GET url and return parsed JSON, or None on network/parse failure."""
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        print(f"{Fore.RED}❌ Network error: {e}")
        return None
    try:
        return response.json()
    except ValueError:
        print(f"{Fore.RED}❌ Invalid response from weather service.")
        return None


def _api_ok(data):
    """Return True if the API response indicates success (cod 200)."""
    return str(data.get("cod")) == "200"


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
    Extracts the minimum and maximum temperatures from the given weather data,
    converts them from Kelvin to Fahrenheit, and returns them as a tuple.

    Args:
        weather_data (dict): The weather data dictionary, expected to contain 'main' with 'temp_min' and 'temp_max'.

    Returns:
        tuple: (min_temperature_fahrenheit, max_temperature_fahrenheit)
    """
    # Use get with defaults and provide error handling in case of bad input
    try:
        main_data = weather_data.get('main', {})
        min_temp_kelvin = main_data.get('temp_min')
        max_temp_kelvin = main_data.get('temp_max')
        if min_temp_kelvin is None or max_temp_kelvin is None:
            raise ValueError("Temperature data missing from weather_data['main']")
        min_temp_f = kelvin_to_fahrenheit(min_temp_kelvin)
        max_temp_f = kelvin_to_fahrenheit(max_temp_kelvin)
        return min_temp_f, max_temp_f
    except Exception as e:
        print(f"{Fore.RED}Error extracting min/max temperature: {e}")
        return None, None

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
    forecast_data = _fetch_json(_build_url(FORECAST_BASE_URL, city_name))
    if forecast_data is None:
        return

    if not _api_ok(forecast_data):
        forecast_error_message = forecast_data.get("message", "Unknown error here")
        print(f"{Fore.RED}❌ Error: {forecast_error_message}")
        return

    days = defaultdict(list)
    for entry in forecast_data.get("list", []):
        dt_txt = entry.get("dt_txt")
        if not dt_txt:
            continue
        date = dt_txt.split(" ")[0]
        days[date].append(entry)

    forecast_city = forecast_data.get("city", {}).get("name", "Unknown City")
    forecast_country = forecast_data.get("city", {}).get("country", "Unknown Country")
    forecast_location = f"{forecast_city}, {forecast_country}"

    table_data = []
    for date in sorted(days.keys())[:3]:
        entries = days[date]
        first_entry = entries[0]

        min_temps = []
        max_temps = []
        for entry in entries:
            main = entry.get("main", {})
            temp_min = main.get("temp_min")
            temp_max = main.get("temp_max")
            if temp_min is not None:
                min_temps.append(kelvin_to_fahrenheit(temp_min))
            if temp_max is not None:
                max_temps.append(kelvin_to_fahrenheit(temp_max))

        if not min_temps or not max_temps:
            continue

        min_temp_actual = min(min_temps)
        max_temp_actual = max(max_temps)
        forecast_date = first_entry["dt"]
        weather_condition = first_entry["weather"][0]["description"]
        precipitation = max(entry.get("pop", 0) for entry in entries) * 100
        humidity = first_entry["main"]["humidity"]

        table_data.append([
            f"{Fore.WHITE}📅 {convert_date_time(forecast_date)}",
            f"{Fore.CYAN}📍 {forecast_location}",
            f"{Fore.BLUE}🌡️  ↘️  {min_temp_actual}°F",
            f"{Fore.BLUE}🌡️  ↗️  {max_temp_actual}°F ",
            f"{Fore.WHITE}{weather_condition} ☁️ ",
            f"{Fore.BLUE}{precipitation:.1f}% 🌧️ ",
            f"{Fore.MAGENTA}{humidity}% 💧{Style.RESET_ALL}",
        ])

    if not table_data:
        print(f"{Fore.RED}❌ Error: No forecast data available.")
        return

    weather_headers = ["Date", "Location", "Min Temp", "Max Temp", "Condition", "Precipitation", "Humidity"]
    print(tabulate(table_data, headers=weather_headers, tablefmt="grid"))

# Function to fetch and display the current weather
def get_weather(city_name):
    """
    Fetch the current weather for the given city
    Display the weather data as a formatted table with colorful output
    """
    weather_data = _fetch_json(_build_url(BASE_URL, city_name))
    if weather_data is None:
        return

    if not _api_ok(weather_data):
        weather_error_message = weather_data.get("message", "Unknown error here")
        print(f"{Fore.RED}❌ Error: {weather_error_message}")
        return

    weather_date = weather_data['dt']  # Get the Unix timestamp for the current weather
    weather_location = weather_data['name']  # Get city name
    min_temp_actual, max_temp_actual = grab_min_max_temp(weather_data)
    if min_temp_actual is None or max_temp_actual is None:
        return
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
