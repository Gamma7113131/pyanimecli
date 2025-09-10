import sys
import argparse
import requests
import platform
import subprocess
import tempfile
import shutil
import os
import re
from urllib.parse import quote
from tqdm import tqdm
try:
    from pym3u8downloader import M3U8Downloader
except ImportError:
    M3U8Downloader = None
    
try:
    from packaging import version as semver
except ImportError:
    semver = None

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.live import Live
    from rich.spinner import Spinner
except ImportError:
    print("Error: The 'rich' library is required. Please install it using 'pip install rich'.")
    sys.exit(1)

__version__ = "1.1"
PACKAGE_NAME = "pyanimecli"

console = Console()

BASE_URL = "https://yumaapi.vercel.app"
PROXY_URL = "https://gammam3u8proxy-fxsb.vercel.app/cors?url="

def proxy_url(url):
    if not url:
        return ""
    return f"{PROXY_URL}{url}"

def make_request(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    spinner = Spinner("dots", text=Text(f"Fetching data from {url}...", style="cyan"))
    with Live(spinner, console=console, transient=True, refresh_per_second=20):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]API Request Error:[/bold red] {e}")
            return None
        except ValueError:
            console.print("[bold red]API Error:[/bold red] Failed to decode JSON from response.")
            return None

def clean_description(description):
    if not description:
        return "No description available."
    cleaned = re.sub(r'(\r\n)?\r?\n?\[Written by MAL Rewrite\]', '', description, flags=re.IGNORECASE).strip()
    return cleaned

def check_executable(name):
    return shutil.which(name) is not None

def display_search_results(results, title="Search Results"):
    if not results or not results.get("results"):
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(title=f"[bold cyan]{title}[/bold cyan]", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=40)
    table.add_column("Title", style="bold white", min_width=20)
    table.add_column("Type", style="green", width=8)
    table.add_column("Sub", style="blue", width=5)
    table.add_column("Dub", style="red", width=5)
    table.add_column("Duration", style="yellow", width=10)

    for item in results["results"]:
        table.add_row(
            item.get("id", "N/A"),
            item.get("title", "N/A"),
            item.get("type", "N/A"),
            str(item.get("sub", "0")),
            str(item.get("dub", "0")),
            item.get("duration", "N/A")
        )

    console.print(table)
    console.print(f"Page [bold]{results.get('current_page', 1)}[/bold] of [bold]{results.get('total_pages', 1)}[/bold]. Use -p <page_number> to navigate.")

def display_anime_info(info):
    if not info:
        console.print("[bold red]Could not retrieve anime info.[/bold red]")
        return

    title = info.get("title", "No Title")
    description = clean_description(info.get("description"))
    
    info_text = Text()
    info_text.append(f"ID: ", style="bold magenta")
    info_text.append(f"{info.get('id', 'N/A')}\n")
    info_text.append(f"Type: ", style="bold magenta")
    info_text.append(f"{info.get('type', 'N/A')}\n")
    info_text.append(f"Total Episodes: ", style="bold magenta")
    info_text.append(f"{info.get('total_episodes', 'N/A')}\n")
    info_text.append(f"Sub Episodes: ", style="bold magenta")
    info_text.append(f"{info.get('sub', 'N/A')}\n")
    info_text.append(f"Dub Episodes: ", style="bold magenta")
    info_text.append(f"{info.get('dub', 'N/A')}\n")
    info_text.append(f"Status: ", style="bold magenta")
    info_text.append(f"{info.get('status', 'N/A')}\n")
    info_text.append(f"Genres: ", style="bold magenta")
    info_text.append(f"{', '.join(info.get('genres', ['N/A']))}\n")
    info_text.append(f"Image: ", style="bold magenta")
    info_text.append(proxy_url(info.get('image', '')), style="cyan underline")

    console.print(Panel(info_text, title=f"[bold green]{title}[/bold green]", border_style="green", expand=False))
    console.print(Panel(description, title="[bold]Description[/bold]", border_style="blue"))
    
    episodes = info.get("episodes", [])
    if episodes:
        episode_table = Table(title="[bold cyan]Episodes[/bold cyan]", show_header=True, header_style="bold magenta")
        episode_table.add_column("Ep #", style="dim")
        episode_table.add_column("Title", style="bold white")
        episode_table.add_column("Episode ID", style="dim")

        for ep in episodes:
            episode_table.add_row(
                str(ep.get("number", "N/A")),
                ep.get("title", "N/A"),
                ep.get("id", "N/A")
            )
        console.print(episode_table)
        console.print("Use -w <Episode ID> <sub|dub> to watch.")

def sanitize_filename(name):
    if not name:
        return "download"
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', '_', name)
    return name.strip()

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def install_ffmpeg_windows():
    try:
        console.print("Attempting to install FFmpeg using Chocolatey...")
        subprocess.run(["choco", "install", "ffmpeg", "-y"], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[yellow]Chocolatey installation failed.[/yellow]")
        console.print("\nTo install FFmpeg manually:")
        console.print("1. Visit [link=https://github.com/BtbN/FFmpeg-Builds/releases]https://github.com/BtbN/FFmpeg-Builds/releases[/link]")
        console.print("2. Download the latest ffmpeg-master-latest-win64-gpl.zip")
        console.print("3. Extract the contents")
        console.print("4. Add the bin folder to your system's PATH environment variable")
        return False

def download_episode(episode_id, download_type, output_path=None):
    if not check_ffmpeg():
        console.print("[bold red]FFmpeg is required but not found.[/bold red]")
        if platform.system() == "Windows":
            response = input("Would you like to attempt automatic installation? (y/n): ").lower()
            if response == 'y':
                if not install_ffmpeg_windows():
                    return
            else:
                return
        else:
            console.print("Please install FFmpeg using your system's package manager.")
            return

    if not output_path:
        console.print("Auto-generating filename (requires fetching anime info)...")
        try:
            anime_id = episode_id.split("$episode$")[0]
            anime_info = make_request(f"info/{anime_id}")
            if not anime_info:
                raise ValueError("Failed to get anime info for filename generation.")
            
            anime_title = anime_info.get("title", "Unknown_Anime")
            ep_num = "Unknown"
            for ep in anime_info.get("episodes", []):
                if ep.get("id") == episode_id:
                    ep_num = str(ep.get("number", "Unknown")).zfill(2)
                    break
            
            safe_title = sanitize_filename(anime_title)
            output_path = f"./{safe_title}-Episode-{ep_num}-[{download_type}].mp4"
        except Exception as e:
            console.print(f"[bold red]Could not generate filename:[/bold red] {e}. Aborting download.")
            return

    console.print(f"Preparing to download to: [green]{os.path.abspath(output_path)}[/green]")
    console.print("Fetching stream data...")
    stream_data = make_request("watch", params={"episodeId": episode_id, "type": download_type})

    if not stream_data or not stream_data.get("sources"):
        console.print("[bold red]Could not retrieve stream sources for download.[/bold red]")
        return

    stream_url = stream_data["sources"][0].get("url")
    if not stream_url:
        console.print("[bold red]Incomplete stream data received.[/bold red]")
        return
    
    proxied_stream_url = proxy_url(stream_url)
    
    try:
        # Get video duration for progress bar
        probe_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            proxied_stream_url
        ]
        
        try:
            duration = float(subprocess.check_output(probe_cmd).decode().strip())
        except:
            duration = 0  # If duration can't be determined, progress bar will be indeterminate
            console.print("[yellow]Could not determine video duration. Progress will be shown without time estimation.[/yellow]")

        console.print("Starting video download...")

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-i", proxied_stream_url,  # Input file
            "-c", "copy",  # Copy streams without re-encoding
            "-bsf:a", "aac_adtstoasc",  # Fix audio stream format if needed
            output_path  # Output file
        ]

        process = subprocess.Popen(ffmpeg_cmd, stderr=subprocess.PIPE, universal_newlines=True)
        time_pattern = re.compile(r'time=(\d+):(\d+):(\d+\.?\d*)')

        with tqdm(total=duration, unit="sec", desc="Downloading", disable=None) as pbar:
            for line in process.stderr:
                match = time_pattern.search(line)
                if match:
                    h, m, s = match.groups()
                    seconds = int(h) * 3600 + int(m) * 60 + float(s)
                    pbar.n = min(seconds, duration)
                    pbar.refresh()

        process.wait()

        if process.returncode == 0:
            console.print(f"\n[bold green]Video download complete![/bold green]")
        else:
            raise subprocess.CalledProcessError(process.returncode, ffmpeg_cmd)

    except Exception as e:
        console.print(f"[bold red]An error occurred during video download:[/bold red] {e}")
        return

    if download_type == "sub" and stream_data.get("subtitles"):
        sub_url = stream_data["subtitles"][0].get("url")
        if sub_url:
            sub_filename = os.path.splitext(output_path)[0] + ".vtt"
            console.print(f"Downloading subtitles to [cyan]{sub_filename}[/cyan]...")
            try:
                proxied_sub_url = proxy_url(sub_url)
                sub_response = requests.get(proxied_sub_url)
                sub_response.raise_for_status()
                with open(sub_filename, 'wb') as f:
                    f.write(sub_response.content)
                console.print("[green]Subtitle download complete.[/green]")
            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]Failed to download subtitles:[/bold red] {e}")
                
def get_and_download_episode(anime_id, ep_num_str, download_type, output_path=None):
    try:
        episode_number = int(ep_num_str)
    except ValueError:
        console.print(f"[bold red]Error:[/bold red] Episode number must be an integer. You provided '{ep_num_str}'.")
        return

    console.print(f"Fetching info for anime [cyan]{anime_id}[/cyan] to find episode {episode_number}...")
    data = make_request(f"info/{anime_id}")

    if not data or not data.get("episodes"):
        console.print(f"[bold red]Could not retrieve info or episode list for anime ID '{anime_id}'.[/bold red]")
        return

    target_episode = next((ep for ep in data["episodes"] if ep.get("number") is not None and int(ep.get("number")) == episode_number), None)

    if target_episode and target_episode.get("id"):
        episode_id = target_episode["id"]
        console.print(f"Found Episode ID: [green]{episode_id}[/green]. Proceeding to download...")
        
        if not output_path:
            anime_title = data.get("title", "Unknown_Anime")
            ep_num = str(target_episode.get("number", "Unknown")).zfill(2)
            safe_title = sanitize_filename(anime_title)
            output_path = f"./{safe_title}-Episode-{ep_num}-[{download_type}].mp4"

        download_episode(episode_id, download_type, output_path)
    else:
        console.print(f"[bold red]Could not find episode number {episode_number} for this anime.[/bold red]")
        console.print("Use the -i <anime_id> command to see a list of available episodes.")

def check_for_updates():
    if semver is None:
        console.print("[yellow]Skipping update check: 'packaging' library not found. Install with 'pip install packaging'[/yellow]")
        return
    try:
        console.print("Checking for updates...")
        url = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        latest_version_str = response.json()["info"]["version"]

        current_version = semver.parse(__version__)
        latest_version = semver.parse(latest_version_str)

        if latest_version > current_version:
            console.print(f"\n[bold yellow]A new version is available: {latest_version_str}[/bold yellow]")
            console.print(f"To update, run: [cyan]pip install --upgrade {PACKAGE_NAME}[/cyan]")
        else:
            console.print("[green]You are using the latest version.[/green]")
    except Exception:
        console.print("[yellow]Could not check for updates.[/yellow]")

def get_and_watch_episode(anime_id, ep_num_str, watch_type):
    try:
        episode_number = int(ep_num_str)
    except ValueError:
        console.print(f"[bold red]Error:[/bold red] Episode number must be an integer. You provided '{ep_num_str}'.")
        return

    console.print(f"Fetching info for anime [cyan]{anime_id}[/cyan] to find episode {episode_number}...")
    endpoint = f"info/{anime_id}"
    data = make_request(endpoint)

    if not data or not data.get("episodes"):
        console.print(f"[bold red]Could not retrieve info or episode list for anime ID '{anime_id}'.[/bold red]")
        return

    target_episode = None
    for ep in data["episodes"]:
        if ep.get("number") is not None and int(ep.get("number")) == episode_number:
            target_episode = ep
            break

    if target_episode and target_episode.get("id"):
        episode_id = target_episode["id"]
        console.print(f"Found Episode ID: [green]{episode_id}[/green]. Proceeding to watch...")
        watch_episode(episode_id, watch_type)
    else:
        console.print(f"[bold red]Could not find episode number {episode_number} for this anime.[/bold red]")
        console.print("Use the -i <anime_id> command to see a list of available episodes.")

def display_spotlight(spotlight_data):
    if not spotlight_data:
        console.print("[yellow]No spotlight data found.[/yellow]")
        return
    
    console.print("[bold yellow]🌟 Spotlight 🌟[/bold yellow]")
    for item in spotlight_data:
        rank = item.get("other_data", {}).get("rank", "")
        title = item.get("title", "N/A")
        description = clean_description(item.get("other_data", {}).get("description", ""))
        release_date = item.get("other_data", {}).get("releaseDate", "N/A")

        panel_content = Text()
        panel_content.append(f"ID: ", style="bold magenta")
        panel_content.append(f"{item.get('id', 'N/A')}\n")
        panel_content.append(f"Release Date: ", style="bold magenta")
        panel_content.append(f"{release_date}\n\n")
        panel_content.append(description)

        console.print(Panel(
            panel_content,
            title=f"[bold green]{rank}: {title}[/bold green]",
            border_style="green"
        ))

def display_schedule(schedule_data, date):
    if not schedule_data:
        console.print(f"[yellow]No schedule found for {date}.[/yellow]")
        return
    
    table = Table(title=f"[bold cyan]Airing Schedule for {date}[/bold cyan]", show_header=True, header_style="bold magenta")
    table.add_column("Time (UTC)", style="yellow")
    table.add_column("Title", style="bold white")
    table.add_column("Airing Episode", style="green")
    table.add_column("ID", style="dim")

    for item in schedule_data:
        other_data = item.get("other_data", {})
        table.add_row(
            other_data.get("airingTime", "N/A"),
            item.get("title", "N/A"),
            other_data.get("airingEpisode", "N/A"),
            item.get("id", "N/A")
        )
    console.print(table)

def display_suggestions(suggestions_data):
    if not suggestions_data:
        console.print("[yellow]No suggestions found.[/yellow]")
        return

    table = Table(title="[bold cyan]Search Suggestions[/bold cyan]", show_header=True, header_style="bold magenta")
    table.add_column("Title", style="bold white")
    table.add_column("Alias", style="dim")
    table.add_column("Release Date", style="green")
    table.add_column("ID", style="dim")
    
    for item in suggestions_data:
        other_data = item.get("other_data", {})
        table.add_row(
            item.get("title", "N/A"),
            other_data.get("alias", "N/A"),
            other_data.get("releaseDate", "N/A"),
            item.get("id", "N/A")
        )
    console.print(table)
    
def search_anime(query, page):
    endpoint = f"search/{quote(query)}"
    data = make_request(endpoint, params={"page": page, "max_results": 10})
    if data:
        display_search_results(data)

def get_anime_info(anime_id):
    endpoint = f"info/{anime_id}"
    data = make_request(endpoint)
    if data:
        display_anime_info(data)

def watch_episode(episode_id, watch_type):
    if not check_executable("vlc"):
        console.print("[bold red]VLC not found.[/bold red] Please install it from 'https://www.videolan.org/vlc' and ensure it's in your system's PATH.")
        return

    is_windows = platform.system() == "Windows"
    downloader = "curl" if is_windows else "wget"

    if not check_executable(downloader):
        console.print(f"[bold red]{downloader.capitalize()} not found.[/bold red] Please install it and ensure it's in your system's PATH.")
        return

    endpoint = "watch"
    params = {"episodeId": episode_id, "type": watch_type}
    data = make_request(endpoint, params=params)

    if not data or not data.get("sources"):
        console.print("[bold red]Could not retrieve stream sources.[/bold red]")
        return

    stream_url = data["sources"][0].get("url")
    referrer = data["headers"].get("Referer")
    
    if not stream_url or not referrer:
        console.print("[bold red]Incomplete stream data received.[/bold red]")
        return
    
    proxied_stream_url = proxy_url(stream_url)
    vlc_command = ["vlc", proxied_stream_url, f"--http-referrer={referrer}"]
    
    sub_file_path = None
    if watch_type == "sub" and data.get("subtitles"):
        subs = data["subtitles"]
        chosen_sub = None
    
        if len(subs) == 1:
            chosen_sub = subs[0]
            console.print(f"Only one subtitle available: [cyan]{chosen_sub['lang']}[/cyan]")
        else:
            console.print("\nAvailable subtitles:")
            for idx, sub in enumerate(subs, start=1):
                console.print(f"[{idx}] {sub['lang']}")
            
            while True:
                try:
                    choice = int(input("\nEnter the number of the subtitle you want: "))
                    if 1 <= choice <= len(subs):
                        chosen_sub = subs[choice - 1]
                        break
                    else:
                        console.print("[bold red]Invalid choice. Try again.[/bold red]")
                except ValueError:
                    console.print("[bold red]Please enter a valid number.[/bold red]")
    
        if chosen_sub:
            sub_url = chosen_sub.get("url")
            if sub_url:
                proxied_sub_url = proxy_url(sub_url)
                
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".vtt") as tmp_file:
                    sub_file_path = tmp_file.name
    
                console.print(f"Downloading subtitles ([cyan]{chosen_sub['lang']}[/cyan]) to [cyan]{sub_file_path}[/cyan]...")
    
                if is_windows:
                    download_cmd = ["curl", "-s", "-L", "-o", sub_file_path, proxied_sub_url]
                else:
                    download_cmd = ["wget", "-q", "-O", sub_file_path, proxied_sub_url]
    
                try:
                    subprocess.run(download_cmd, check=True)
                    vlc_command.append(f"--sub-file={sub_file_path}")
                    console.print("[green]Subtitle download complete.[/green]")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    console.print(f"[bold red]Failed to download subtitles:[/bold red] {e}")
                    sub_file_path = None

    command_str = ' '.join(f'"{c}"' if ' ' in c else c for c in vlc_command)
    console.print(f"\n[bold]Executing command:[/bold]\n[yellow]{command_str}[/yellow]\n")

    try:
        subprocess.run(vlc_command)
    except Exception as e:
        console.print(f"[bold red]Failed to launch VLC:[/bold red] {e}")
    finally:
        if sub_file_path and os.path.exists(sub_file_path):
            os.remove(sub_file_path)

def get_recent_episodes(page):
    data = make_request("recent-episodes", params={"page": page})
    if data:
        display_search_results(data, title="Recently Updated Episodes")

def get_top_airing(page):
    data = make_request("top-airing", params={"page": page})
    if data:
        display_search_results(data, title="Top Airing Anime")

def list_genres():
    data = make_request("genre/list")
    if data:
        console.print(Panel(", ".join(data), title="[bold cyan]Available Genres[/bold cyan]", border_style="cyan"))

def search_by_genre(genre, page):
    endpoint = f"genre/{quote(genre)}"
    data = make_request(endpoint, params={"page": page})
    if data:
        display_search_results(data, title=f"Results for Genre: {genre.capitalize()}")

def search_by_studio(studio_id, page):
    endpoint = f"studio/{quote(studio_id)}"
    data = make_request(endpoint, params={"page": page})
    if data:
        display_search_results(data, title=f"Results for Studio: {studio_id}")

def get_schedule(date):
    endpoint = f"schedule/{date}"
    data = make_request(endpoint)
    if data is not None:
        display_schedule(data, date)

def get_spotlight():
    data = make_request("spotlight")
    if data:
        display_spotlight(data)

def get_search_suggestions(query):
    endpoint = f"search-suggestions/{quote(query)}"
    data = make_request(endpoint)
    if data:
        display_suggestions(data)

def display_help(command=None):
    console.print(Panel(f"[bold yellow]pyanimecli v{__version__} - A CLI for Watching & Downloading Anime[/bold yellow]", expand=False, border_style="yellow"))
    
    help_data = {
        "search": ("-s, -search <query>", "Search for an anime."),
        "info": ("-i, -info <id>", "Get detailed information about an anime by its ID."),
        "watch": ("-w, -watch <id> <ep#> <type> | <ep_id> <type>", "Watch an episode using VLC."),
        "download": ("-d, -download <id> <ep#> <type> [out] | <ep_id> <type> [out]", "Download an episode. '[out]' is an optional file path."),
        "recent": ("-re, -recent-episodes", "List recently updated episodes."),
        "top_airing": ("-ta, -top-airing", "List top airing anime."),
        "genres": ("-g, -genres", "List all available genres."),
        "genre_search": ("-gs, -genre-search <genre>", "Search for anime by a specific genre."),
        "studio": ("-st, -studio <studio_id>", "Search for anime by a studio ID."),
        "schedule": ("-sc, -schedule <YYYY-MM-DD>", "Get the airing schedule for a specific date."),
        "spotlight": ("-sp, -spotlight", "Show spotlight anime."),
        "suggestions": ("-ss, -search-suggestions <query>", "Get search suggestions for a query."),
        "pagination": ("-p, -page <number>", "Used with commands that support pages (search, recent, etc.)."),
        "version": ("-v, -version", "Show the script version and check for updates.")
    }

    if command and command in help_data:
        usage, desc = help_data[command]
        console.print(f"\n[bold]Help for '{command}':[/bold]")
        console.print(f"  [cyan]Usage:[/cyan] {usage}")
        console.print(f"  [cyan]Description:[/cyan] {desc}")
    else:
        table = Table(title="[bold]Available Commands[/bold]", show_header=False, box=None)
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description")
        for key, (usage, desc) in help_data.items():
            table.add_row(usage, desc)
        console.print(table)
        console.print("\nUse -h <command_name> (e.g., -h download) for specific command help.")
        
def main():
    parser = argparse.ArgumentParser(description=f"pyanimecli v{__version__} - A CLI for anime.", add_help=False)
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-s', '-search', dest='search', nargs='+', help='Search for an anime.')
    group.add_argument('-i', '-info', dest='info', help='Get info for an anime by ID.')
    group.add_argument('-w', '-watch', dest='watch', nargs='+', metavar=('ID', '...'), help='Watch an episode. See -h watch.')
    group.add_argument('-d', '-download', dest='download', nargs='+', metavar=('ID', '...'), help='Download an episode. See -h download.')
    group.add_argument('-re', '-recent-episodes', dest='recent', action='store_true', help='Get recent episodes.')
    group.add_argument('-ta', '-top-airing', dest='top_airing', action='store_true', help='Get top airing anime.')
    group.add_argument('-g', '-genres', dest='genres', action='store_true', help='List all genres.')
    group.add_argument('-gs', '-genre-search', dest='genre_search', nargs='+', help='Search by genre.')
    group.add_argument('-st', '-studio', dest='studio', nargs='+', help='Search by studio.')
    group.add_argument('-sc', '-schedule', dest='schedule', help='Get schedule for a date (YYYY-MM-DD).')
    group.add_argument('-sp', '-spotlight', dest='spotlight', action='store_true', help='Get spotlight anime.')
    group.add_argument('-ss', '-search-suggestions', dest='suggestions', nargs='+', help='Get search suggestions.')
    group.add_argument('-h', '-help', dest='help', nargs='?', const='all', help='Show help message.')
    group.add_argument('-v', '-version', dest='version', action='store_true', help='Show script version.')

    parser.add_argument('-p', '-page', dest='page', type=int, default=1, help='Page number for paginated results.')

    if len(sys.argv) == 1:
        display_help()
        sys.exit(0)

    try:
        args = parser.parse_args()
        
        if args.help:
            cmd_map = {
                "search": "search", "s": "search", "info": "info", "i": "info",
                "watch": "watch", "w": "watch", "download": "download", "d": "download",
                "recent": "recent", "re": "recent", "recent-episodes": "recent",
                "top": "top_airing", "ta": "top_airing", "top-airing": "top_airing",
                "genres": "genres", "g": "genres", "genre-search": "genre_search", "gs": "genre_search",
                "studio": "studio", "st": "studio", "schedule": "schedule", "sc": "schedule",
                "spotlight": "spotlight", "sp": "spotlight",
                "suggestions": "suggestions", "ss": "suggestions", "search-suggestions": "suggestions",
                "page": "pagination", "p": "pagination", "version": "version", "v": "version",
            }
            command_to_help = cmd_map.get(args.help) if args.help != 'all' else None
            display_help(command_to_help)
        elif args.version:
            console.print(f"pyanimecli version [bold cyan]{__version__}[/bold cyan]")
            check_for_updates()
        elif args.search:
            search_anime(' '.join(args.search), args.page)
        elif args.info:
            get_anime_info(args.info)
        elif args.watch:
            first_arg = args.watch[0]
            if "$episode$" in first_arg:
                if len(args.watch) == 2:
                    watch_episode(args.watch[0], args.watch[1].lower())
                else:
                    console.print("[bold red]Invalid Usage:[/bold red] Use: <episode_id> <sub|dub>")
                    display_help('watch')
            else:
                if len(args.watch) == 3:
                    get_and_watch_episode(args.watch[0], args.watch[1], args.watch[2].lower())
                else:
                    console.print("[bold red]Invalid Usage:[/bold red] Use: <anime_id> <ep_num> <sub|dub>")
                    display_help('watch')
        elif args.download:
            args_list = args.download
            first_arg = args_list[0]
            is_full_id = "$episode$" in first_arg
            if is_full_id:
                if len(args_list) not in [2, 3]:
                    console.print("[bold red]Invalid Usage:[/bold red] Use: <episode_id> <type> [output_path]")
                    display_help('download')
                    return
                episode_id, dl_type = args_list[0], args_list[1]
                output_path = args_list[2] if len(args_list) == 3 else None
                download_episode(episode_id, dl_type.lower(), output_path)
            else:
                if len(args_list) not in [3, 4]:
                    console.print("[bold red]Invalid Usage:[/bold red] Use: <anime_id> <ep_num> <type> [output_path]")
                    display_help('download')
                    return
                anime_id, ep_num_str, dl_type = args_list[0], args_list[1], args_list[2]
                output_path = args_list[3] if len(args_list) == 4 else None
                get_and_download_episode(anime_id, ep_num_str, dl_type.lower(), output_path)
        elif args.recent:
            get_recent_episodes(args.page)
        elif args.top_airing:
            get_top_airing(args.page)
        elif args.genres:
            list_genres()
        elif args.genre_search:
            search_by_genre(' '.join(args.genre_search), args.page)
        elif args.studio:
            search_by_studio(' '.join(args.studio), args.page)
        elif args.schedule:
            get_schedule(args.schedule)
        elif args.spotlight:
            get_spotlight()
        elif args.suggestions:
            get_search_suggestions(' '.join(args.suggestions))
        else:
             display_help()

    except argparse.ArgumentError as e:
        console.print(f"[bold red]Argument Error:[/bold red] {e}")
        display_help()
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
        
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
