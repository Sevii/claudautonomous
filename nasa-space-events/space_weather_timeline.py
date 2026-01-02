#!/usr/bin/env python3
"""
NASA DONKI Space Weather Timeline Visualization

Fetches Solar Flares (FLR), Coronal Mass Ejections (CME), and Geomagnetic Storms (GST)
from NASA's DONKI API and plots them on a timeline to visualize the delay between
solar explosions and their Earth impact.

API Documentation: https://ccmc.gsfc.nasa.gov/tools/DONKI/
"""

import requests
from datetime import datetime, timedelta
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
from dataclasses import dataclass


# NASA API configuration
NASA_API_KEY = "DEMO_KEY"  # Replace with your API key for higher rate limits
BASE_URL = "https://api.nasa.gov/DONKI"


@dataclass
class SpaceEvent:
    """Represents a space weather event."""
    event_id: str
    event_type: str  # 'FLR', 'CME', or 'GST'
    start_time: datetime
    end_time: Optional[datetime]
    intensity: str  # Flare class, CME type, or Kp index
    linked_events: list


def fetch_solar_flares(start_date: str, end_date: str) -> list[SpaceEvent]:
    """Fetch Solar Flare (FLR) data from DONKI API."""
    url = f"{BASE_URL}/FLR"
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "api_key": NASA_API_KEY
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    events = []
    for flare in data:
        start = datetime.fromisoformat(flare["beginTime"].replace("Z", "+00:00"))
        end = None
        if flare.get("endTime"):
            end = datetime.fromisoformat(flare["endTime"].replace("Z", "+00:00"))

        # Get flare class (e.g., M1.5, X2.0)
        intensity = flare.get("classType", "Unknown")

        linked = []
        if flare.get("linkedEvents"):
            linked = [e.get("activityID", "") for e in flare["linkedEvents"]]

        events.append(SpaceEvent(
            event_id=flare["flrID"],
            event_type="FLR",
            start_time=start,
            end_time=end,
            intensity=intensity,
            linked_events=linked
        ))

    return events


def fetch_cme(start_date: str, end_date: str) -> list[SpaceEvent]:
    """Fetch Coronal Mass Ejection (CME) data from DONKI API."""
    url = f"{BASE_URL}/CME"
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "api_key": NASA_API_KEY
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    events = []
    for cme in data:
        start = datetime.fromisoformat(cme["startTime"].replace("Z", "+00:00"))

        # CMEs don't have a simple end time, use analysis data if available
        end = None
        intensity = "N/A"

        # Get CME analysis info for speed/type
        if cme.get("cmeAnalyses"):
            analysis = cme["cmeAnalyses"][0]  # Get first analysis
            speed = analysis.get("speed", 0)
            cme_type = analysis.get("type", "Unknown")
            intensity = f"{cme_type} ({speed} km/s)"

        linked = []
        if cme.get("linkedEvents"):
            linked = [e.get("activityID", "") for e in cme["linkedEvents"]]

        events.append(SpaceEvent(
            event_id=cme["activityID"],
            event_type="CME",
            start_time=start,
            end_time=end,
            intensity=intensity,
            linked_events=linked
        ))

    return events


def fetch_geomagnetic_storms(start_date: str, end_date: str) -> list[SpaceEvent]:
    """Fetch Geomagnetic Storm (GST) data from DONKI API."""
    url = f"{BASE_URL}/GST"
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "api_key": NASA_API_KEY
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    events = []
    for storm in data:
        start = datetime.fromisoformat(storm["startTime"].replace("Z", "+00:00"))

        # Get Kp index (measure of geomagnetic activity)
        intensity = "Unknown"
        if storm.get("allKpIndex"):
            max_kp = max(storm["allKpIndex"], key=lambda x: x.get("kpIndex", 0))
            intensity = f"Kp {max_kp.get('kpIndex', 'N/A')}"

        linked = []
        if storm.get("linkedEvents"):
            linked = [e.get("activityID", "") for e in storm["linkedEvents"]]

        events.append(SpaceEvent(
            event_id=storm["gstID"],
            event_type="GST",
            start_time=start,
            end_time=None,
            intensity=intensity,
            linked_events=linked
        ))

    return events


def create_timeline_chart(flares: list[SpaceEvent],
                          cmes: list[SpaceEvent],
                          storms: list[SpaceEvent],
                          title: str = "Space Weather Timeline",
                          save_path: str = None):
    """
    Create a timeline/Gantt chart showing solar flares, CMEs, and geomagnetic storms.
    Visualizes the propagation delay from solar events to Earth impact.
    """
    fig, ax = plt.subplots(figsize=(16, 10))

    # Define colors and y-positions for each event type
    event_config = {
        "FLR": {"color": "#FF6B6B", "y": 3, "label": "Solar Flares (FLR)"},
        "CME": {"color": "#4ECDC4", "y": 2, "label": "Coronal Mass Ejections (CME)"},
        "GST": {"color": "#9B59B6", "y": 1, "label": "Geomagnetic Storms (GST)"}
    }

    # Plot events
    all_dates = []
    event_annotations = []

    def plot_events(events: list[SpaceEvent], config: dict):
        for event in events:
            all_dates.append(event.start_time)

            # Plot event marker
            ax.scatter(event.start_time, config["y"],
                      s=150, c=config["color"],
                      zorder=5, alpha=0.8, edgecolors='white', linewidth=1)

            # Add intensity label
            event_annotations.append({
                'x': event.start_time,
                'y': config["y"],
                'text': event.intensity,
                'color': config["color"]
            })

            # If event has duration, draw a line
            if event.end_time:
                ax.hlines(config["y"], event.start_time, event.end_time,
                         colors=config["color"], linewidth=4, alpha=0.6)

    # Plot all event types
    plot_events(flares, event_config["FLR"])
    plot_events(cmes, event_config["CME"])
    plot_events(storms, event_config["GST"])

    # Draw connections between linked events (solar event -> Earth impact)
    connection_lines = []
    all_events = {e.event_id: e for e in flares + cmes + storms}

    for event in flares + cmes:
        for linked_id in event.linked_events:
            if linked_id in all_events:
                linked_event = all_events[linked_id]
                # Only connect if it's a GST (Earth impact) or CME following a flare
                if linked_event.event_type in ["GST", "CME"]:
                    source_y = event_config[event.event_type]["y"]
                    target_y = event_config[linked_event.event_type]["y"]

                    # Calculate travel time
                    travel_time = linked_event.start_time - event.start_time
                    hours = travel_time.total_seconds() / 3600

                    # Draw connecting arrow
                    ax.annotate(
                        '',
                        xy=(linked_event.start_time, target_y),
                        xytext=(event.start_time, source_y),
                        arrowprops=dict(
                            arrowstyle='->',
                            color='gray',
                            alpha=0.4,
                            connectionstyle='arc3,rad=0.2',
                            linewidth=1.5
                        )
                    )

                    # Add travel time label
                    mid_time = event.start_time + travel_time / 2
                    mid_y = (source_y + target_y) / 2
                    ax.annotate(
                        f'{hours:.1f}h',
                        xy=(mid_time, mid_y),
                        fontsize=7,
                        color='gray',
                        alpha=0.8,
                        ha='center'
                    )

    # Add event intensity annotations (offset to avoid overlap)
    for i, ann in enumerate(event_annotations):
        offset = 0.15 if i % 2 == 0 else -0.25
        ax.annotate(
            ann['text'],
            xy=(ann['x'], ann['y']),
            xytext=(0, 20 if offset > 0 else -20),
            textcoords='offset points',
            fontsize=7,
            rotation=45,
            ha='left',
            color=ann['color'],
            alpha=0.9
        )

    # Configure axes
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(['Geomagnetic Storms\n(Earth Impact)',
                        'Coronal Mass Ejections\n(Solar Corona)',
                        'Solar Flares\n(Sun Surface)'])
    ax.set_ylim(0.5, 3.7)

    # Format x-axis dates
    if all_dates:
        ax.set_xlim(min(all_dates) - timedelta(days=1),
                   max(all_dates) + timedelta(days=1))

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.xticks(rotation=45, ha='right')

    # Add legend
    legend_elements = [
        mpatches.Patch(color=config["color"], label=config["label"], alpha=0.8)
        for config in event_config.values()
    ]
    legend_elements.append(
        plt.Line2D([0], [0], color='gray', alpha=0.4, linewidth=1.5,
                   label='Event Propagation (with travel time)')
    )
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

    # Add grid and labels
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')
    ax.set_xlabel('Date (UTC)', fontsize=11)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # Add explanation text
    fig.text(0.02, 0.02,
             'Solar flares occur on the Sun\'s surface. CMEs are ejections of plasma from the corona.\n'
             'When CMEs reach Earth (1-4 days later), they can cause geomagnetic storms.',
             fontsize=8, style='italic', alpha=0.7)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {save_path}")

    plt.show()

    return fig, ax


def print_event_summary(flares: list[SpaceEvent],
                        cmes: list[SpaceEvent],
                        storms: list[SpaceEvent]):
    """Print a summary of fetched events."""
    print("\n" + "="*60)
    print("SPACE WEATHER EVENT SUMMARY")
    print("="*60)

    print(f"\n🌟 Solar Flares (FLR): {len(flares)} events")
    for flare in sorted(flares, key=lambda x: x.start_time)[:5]:
        print(f"   • {flare.start_time.strftime('%Y-%m-%d %H:%M')} - Class {flare.intensity}")
    if len(flares) > 5:
        print(f"   ... and {len(flares) - 5} more")

    print(f"\n💨 Coronal Mass Ejections (CME): {len(cmes)} events")
    for cme in sorted(cmes, key=lambda x: x.start_time)[:5]:
        print(f"   • {cme.start_time.strftime('%Y-%m-%d %H:%M')} - {cme.intensity}")
    if len(cmes) > 5:
        print(f"   ... and {len(cmes) - 5} more")

    print(f"\n🌍 Geomagnetic Storms (GST): {len(storms)} events")
    for storm in sorted(storms, key=lambda x: x.start_time)[:5]:
        print(f"   • {storm.start_time.strftime('%Y-%m-%d %H:%M')} - {storm.intensity}")
    if len(storms) > 5:
        print(f"   ... and {len(storms) - 5} more")

    # Calculate average propagation time for linked events
    travel_times = []
    all_events = {e.event_id: e for e in flares + cmes + storms}

    for event in cmes:
        for linked_id in event.linked_events:
            if linked_id in all_events:
                linked = all_events[linked_id]
                if linked.event_type == "GST":
                    delta = linked.start_time - event.start_time
                    travel_times.append(delta.total_seconds() / 3600)

    if travel_times:
        avg_time = sum(travel_times) / len(travel_times)
        print(f"\n⏱️  Average CME to Earth travel time: {avg_time:.1f} hours ({avg_time/24:.1f} days)")

    print("\n" + "="*60)


def main():
    """Main function to fetch data and create visualization."""
    # Date range for data (default: last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"Fetching space weather data from {start_str} to {end_str}...")
    print("Using NASA DONKI API (https://api.nasa.gov/DONKI)")
    print("-" * 50)

    try:
        # Fetch all event types
        print("Fetching Solar Flares (FLR)...")
        flares = fetch_solar_flares(start_str, end_str)
        print(f"  Found {len(flares)} solar flares")

        print("Fetching Coronal Mass Ejections (CME)...")
        cmes = fetch_cme(start_str, end_str)
        print(f"  Found {len(cmes)} CMEs")

        print("Fetching Geomagnetic Storms (GST)...")
        storms = fetch_geomagnetic_storms(start_str, end_str)
        print(f"  Found {len(storms)} geomagnetic storms")

        # Print summary
        print_event_summary(flares, cmes, storms)

        # Create timeline visualization
        if flares or cmes or storms:
            print("\nGenerating timeline chart...")
            title = f"Space Weather Events: {start_str} to {end_str}"
            create_timeline_chart(
                flares, cmes, storms,
                title=title,
                save_path="space_weather_timeline.png"
            )
        else:
            print("\nNo events found in the specified date range.")

    except requests.exceptions.RequestException as e:
        print(f"\nError fetching data from NASA API: {e}")
        print("Please check your internet connection and try again.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
