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
import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import numpy as np
from dataclasses import dataclass
from collections import Counter


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


def parse_flare_class(intensity: str) -> tuple[str, float]:
    """Parse flare class into letter and numeric value."""
    match = re.match(r'([ABCMX])(\d+\.?\d*)', intensity)
    if match:
        letter = match.group(1)
        number = float(match.group(2))
        # Convert to numeric scale (A=1, B=2, C=3, M=4, X=5) * intensity
        class_values = {'A': 1, 'B': 2, 'C': 3, 'M': 4, 'X': 5}
        return letter, class_values.get(letter, 0) * 10 + number
    return 'Unknown', 0


def parse_cme_speed(intensity: str) -> float:
    """Extract CME speed from intensity string."""
    match = re.search(r'\((\d+\.?\d*)\s*km/s\)', intensity)
    if match:
        return float(match.group(1))
    return 0


def parse_kp_index(intensity: str) -> float:
    """Extract Kp index from intensity string."""
    match = re.search(r'Kp\s*(\d+\.?\d*)', intensity)
    if match:
        return float(match.group(1))
    return 0


def create_flare_chart(flares: list[SpaceEvent], save_path: str = None):
    """Create individual chart for Solar Flares."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Solar Flare (FLR) Analysis', fontsize=14, fontweight='bold')

    color = '#FF6B6B'

    # Parse flare data
    classes = []
    intensities = []
    times = []
    for flare in flares:
        letter, value = parse_flare_class(flare.intensity)
        if letter != 'Unknown':
            classes.append(letter)
            intensities.append(value)
            times.append(flare.start_time)

    # 1. Timeline of flares with intensity
    ax1 = axes[0, 0]
    if times and intensities:
        scatter = ax1.scatter(times, intensities, c=color, s=80, alpha=0.7, edgecolors='white')
        ax1.set_ylabel('Intensity (class × 10 + value)')
        ax1.set_xlabel('Date')
        ax1.set_title('Solar Flare Timeline by Intensity')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)

        # Add class labels on right y-axis
        ax1_right = ax1.twinx()
        ax1_right.set_ylim(ax1.get_ylim())
        ax1_right.set_yticks([10, 20, 30, 40, 50])
        ax1_right.set_yticklabels(['A', 'B', 'C', 'M', 'X'])
        ax1_right.set_ylabel('Flare Class')

    # 2. Distribution by class
    ax2 = axes[0, 1]
    if classes:
        class_counts = Counter(classes)
        class_order = ['A', 'B', 'C', 'M', 'X']
        counts = [class_counts.get(c, 0) for c in class_order]
        bars = ax2.bar(class_order, counts, color=color, alpha=0.8, edgecolor='white')
        ax2.set_xlabel('Flare Class')
        ax2.set_ylabel('Count')
        ax2.set_title('Distribution by Flare Class')
        ax2.grid(True, axis='y', alpha=0.3)

        # Add count labels on bars
        for bar, count in zip(bars, counts):
            if count > 0:
                ax2.annotate(str(count), xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                           ha='center', va='bottom', fontsize=10)

    # 3. Daily event count
    ax3 = axes[1, 0]
    if times:
        dates = [t.date() for t in times]
        date_counts = Counter(dates)
        sorted_dates = sorted(date_counts.keys())
        counts = [date_counts[d] for d in sorted_dates]
        ax3.bar(sorted_dates, counts, color=color, alpha=0.8, edgecolor='white')
        ax3.set_xlabel('Date')
        ax3.set_ylabel('Number of Flares')
        ax3.set_title('Daily Solar Flare Count')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, axis='y', alpha=0.3)

    # 4. Hourly distribution
    ax4 = axes[1, 1]
    if times:
        hours = [t.hour for t in times]
        ax4.hist(hours, bins=24, range=(0, 24), color=color, alpha=0.8, edgecolor='white')
        ax4.set_xlabel('Hour (UTC)')
        ax4.set_ylabel('Count')
        ax4.set_title('Hourly Distribution of Solar Flares')
        ax4.set_xticks(range(0, 24, 3))
        ax4.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Solar Flare chart saved to: {save_path}")

    plt.show()
    return fig


def create_cme_chart(cmes: list[SpaceEvent], save_path: str = None):
    """Create individual chart for Coronal Mass Ejections."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Coronal Mass Ejection (CME) Analysis', fontsize=14, fontweight='bold')

    color = '#4ECDC4'

    # Parse CME data
    speeds = []
    types = []
    times = []
    for cme in cmes:
        speed = parse_cme_speed(cme.intensity)
        times.append(cme.start_time)
        speeds.append(speed)
        # Extract type (S, C, O, etc.)
        type_match = re.match(r'([A-Z]+)', cme.intensity)
        if type_match:
            types.append(type_match.group(1))
        else:
            types.append('Unknown')

    # 1. Timeline with speed
    ax1 = axes[0, 0]
    if times and speeds:
        valid_idx = [i for i, s in enumerate(speeds) if s > 0]
        valid_times = [times[i] for i in valid_idx]
        valid_speeds = [speeds[i] for i in valid_idx]

        scatter = ax1.scatter(valid_times, valid_speeds, c=color, s=60, alpha=0.7, edgecolors='white')
        ax1.set_ylabel('Speed (km/s)')
        ax1.set_xlabel('Date')
        ax1.set_title('CME Timeline by Speed')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)

        # Add reference lines for CME categories
        ax1.axhline(y=500, color='orange', linestyle='--', alpha=0.5, label='Moderate (500 km/s)')
        ax1.axhline(y=1000, color='red', linestyle='--', alpha=0.5, label='Fast (1000 km/s)')
        ax1.legend(loc='upper right', fontsize=8)

    # 2. Speed distribution histogram
    ax2 = axes[0, 1]
    valid_speeds = [s for s in speeds if s > 0]
    if valid_speeds:
        ax2.hist(valid_speeds, bins=20, color=color, alpha=0.8, edgecolor='white')
        ax2.set_xlabel('Speed (km/s)')
        ax2.set_ylabel('Count')
        ax2.set_title('CME Speed Distribution')
        ax2.axvline(x=np.median(valid_speeds), color='red', linestyle='--',
                   label=f'Median: {np.median(valid_speeds):.0f} km/s')
        ax2.legend()
        ax2.grid(True, axis='y', alpha=0.3)

    # 3. Distribution by type
    ax3 = axes[1, 0]
    if types:
        type_counts = Counter(types)
        sorted_types = sorted(type_counts.keys())
        counts = [type_counts[t] for t in sorted_types]
        bars = ax3.bar(sorted_types, counts, color=color, alpha=0.8, edgecolor='white')
        ax3.set_xlabel('CME Type')
        ax3.set_ylabel('Count')
        ax3.set_title('Distribution by CME Type\n(S=Slow, C=Common, O=Other)')
        ax3.grid(True, axis='y', alpha=0.3)

        for bar, count in zip(bars, counts):
            ax3.annotate(str(count), xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                        ha='center', va='bottom', fontsize=10)

    # 4. Daily CME count
    ax4 = axes[1, 1]
    if times:
        dates = [t.date() for t in times]
        date_counts = Counter(dates)
        sorted_dates = sorted(date_counts.keys())
        counts = [date_counts[d] for d in sorted_dates]
        ax4.bar(sorted_dates, counts, color=color, alpha=0.8, edgecolor='white')
        ax4.set_xlabel('Date')
        ax4.set_ylabel('Number of CMEs')
        ax4.set_title('Daily CME Count')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"CME chart saved to: {save_path}")

    plt.show()
    return fig


def create_gst_chart(storms: list[SpaceEvent], save_path: str = None):
    """Create individual chart for Geomagnetic Storms."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Geomagnetic Storm (GST) Analysis', fontsize=14, fontweight='bold')

    color = '#9B59B6'

    # Parse GST data
    kp_indices = []
    times = []
    for storm in storms:
        kp = parse_kp_index(storm.intensity)
        kp_indices.append(kp)
        times.append(storm.start_time)

    # 1. Timeline with Kp index
    ax1 = axes[0, 0]
    if times and kp_indices:
        ax1.scatter(times, kp_indices, c=color, s=150, alpha=0.8, edgecolors='white', zorder=5)
        ax1.stem(times, kp_indices, linefmt='-', markerfmt=' ', basefmt=' ')
        ax1.set_ylabel('Kp Index')
        ax1.set_xlabel('Date')
        ax1.set_title('Geomagnetic Storm Timeline')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax1.tick_params(axis='x', rotation=45)
        ax1.set_ylim(0, 9)
        ax1.grid(True, alpha=0.3)

        # Add storm intensity bands
        ax1.axhspan(5, 6, alpha=0.2, color='yellow', label='G1 Minor')
        ax1.axhspan(6, 7, alpha=0.2, color='orange', label='G2 Moderate')
        ax1.axhspan(7, 8, alpha=0.2, color='red', label='G3 Strong')
        ax1.axhspan(8, 9, alpha=0.2, color='darkred', label='G4-G5 Severe')
        ax1.legend(loc='upper right', fontsize=8)

    # 2. Kp index distribution
    ax2 = axes[0, 1]
    if kp_indices:
        bins = np.arange(4.5, 9.5, 0.5)
        ax2.hist(kp_indices, bins=bins, color=color, alpha=0.8, edgecolor='white')
        ax2.set_xlabel('Kp Index')
        ax2.set_ylabel('Count')
        ax2.set_title('Kp Index Distribution')
        ax2.grid(True, axis='y', alpha=0.3)

    # 3. Storm severity classification
    ax3 = axes[1, 0]
    if kp_indices:
        severity = []
        for kp in kp_indices:
            if kp < 5:
                severity.append('Below G1')
            elif kp < 6:
                severity.append('G1 Minor')
            elif kp < 7:
                severity.append('G2 Moderate')
            elif kp < 8:
                severity.append('G3 Strong')
            elif kp < 9:
                severity.append('G4 Severe')
            else:
                severity.append('G5 Extreme')

        severity_counts = Counter(severity)
        order = ['Below G1', 'G1 Minor', 'G2 Moderate', 'G3 Strong', 'G4 Severe', 'G5 Extreme']
        colors_map = {'Below G1': 'gray', 'G1 Minor': 'yellow', 'G2 Moderate': 'orange',
                     'G3 Strong': 'red', 'G4 Severe': 'darkred', 'G5 Extreme': 'purple'}

        existing_order = [s for s in order if s in severity_counts]
        counts = [severity_counts[s] for s in existing_order]
        bar_colors = [colors_map[s] for s in existing_order]

        bars = ax3.bar(existing_order, counts, color=bar_colors, alpha=0.8, edgecolor='white')
        ax3.set_xlabel('Storm Severity (NOAA Scale)')
        ax3.set_ylabel('Count')
        ax3.set_title('Geomagnetic Storm Severity Distribution')
        ax3.tick_params(axis='x', rotation=30)
        ax3.grid(True, axis='y', alpha=0.3)

    # 4. Summary stats
    ax4 = axes[1, 1]
    ax4.axis('off')
    if storms:
        stats_text = f"""
        Geomagnetic Storm Statistics
        ─────────────────────────────
        Total Storms: {len(storms)}

        Kp Index:
          • Maximum: {max(kp_indices):.2f}
          • Minimum: {min(kp_indices):.2f}
          • Average: {np.mean(kp_indices):.2f}

        Date Range:
          • First: {min(times).strftime('%Y-%m-%d %H:%M')}
          • Last: {max(times).strftime('%Y-%m-%d %H:%M')}

        Note: Kp index measures global
        geomagnetic activity (0-9 scale).
        G1+ storms (Kp ≥ 5) can affect
        power grids and satellites.
        """
        ax4.text(0.1, 0.5, stats_text, transform=ax4.transAxes, fontsize=11,
                verticalalignment='center', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor=color, alpha=0.2))
    else:
        ax4.text(0.5, 0.5, 'No geomagnetic storms\nin selected period',
                transform=ax4.transAxes, ha='center', va='center', fontsize=14)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Geomagnetic Storm chart saved to: {save_path}")

    plt.show()
    return fig


def create_pairwise_flr_cme(flares: list[SpaceEvent], cmes: list[SpaceEvent], save_path: str = None):
    """Create pairwise comparison chart for Solar Flares and CMEs."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Solar Flares vs Coronal Mass Ejections', fontsize=14, fontweight='bold')

    flr_color = '#FF6B6B'
    cme_color = '#4ECDC4'

    # Build lookup for linked events
    all_events = {e.event_id: e for e in flares + cmes}

    # Find linked FLR-CME pairs
    linked_pairs = []
    for flare in flares:
        for linked_id in flare.linked_events:
            if linked_id in all_events and all_events[linked_id].event_type == 'CME':
                cme = all_events[linked_id]
                linked_pairs.append((flare, cme))

    # 1. Dual timeline
    ax1 = axes[0, 0]
    flr_times = [f.start_time for f in flares]
    cme_times = [c.start_time for c in cmes]

    ax1.scatter(flr_times, [1]*len(flr_times), c=flr_color, s=60, alpha=0.7, label='Solar Flares', edgecolors='white')
    ax1.scatter(cme_times, [0]*len(cme_times), c=cme_color, s=60, alpha=0.7, label='CMEs', edgecolors='white')

    # Draw connections for linked events
    for flare, cme in linked_pairs:
        ax1.annotate('', xy=(cme.start_time, 0), xytext=(flare.start_time, 1),
                    arrowprops=dict(arrowstyle='->', color='gray', alpha=0.3, linewidth=1))

    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(['CME', 'Flare'])
    ax1.set_xlabel('Date')
    ax1.set_title(f'Event Timeline (showing {len(linked_pairs)} linked pairs)')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.tick_params(axis='x', rotation=45)
    ax1.legend(loc='upper right')
    ax1.grid(True, axis='x', alpha=0.3)

    # 2. Daily count comparison
    ax2 = axes[0, 1]
    flr_dates = Counter([t.date() for t in flr_times])
    cme_dates = Counter([t.date() for t in cme_times])
    all_dates = sorted(set(flr_dates.keys()) | set(cme_dates.keys()))

    x = np.arange(len(all_dates))
    width = 0.35

    ax2.bar(x - width/2, [flr_dates.get(d, 0) for d in all_dates], width,
           label='Solar Flares', color=flr_color, alpha=0.8)
    ax2.bar(x + width/2, [cme_dates.get(d, 0) for d in all_dates], width,
           label='CMEs', color=cme_color, alpha=0.8)

    ax2.set_xlabel('Date')
    ax2.set_ylabel('Count')
    ax2.set_title('Daily Event Counts')
    ax2.set_xticks(x[::3])
    ax2.set_xticklabels([d.strftime('%m-%d') for d in all_dates][::3], rotation=45)
    ax2.legend()
    ax2.grid(True, axis='y', alpha=0.3)

    # 3. Flare class vs CME speed for linked events
    ax3 = axes[1, 0]
    if linked_pairs:
        flare_intensities = []
        cme_speeds = []
        for flare, cme in linked_pairs:
            _, intensity = parse_flare_class(flare.intensity)
            speed = parse_cme_speed(cme.intensity)
            if intensity > 0 and speed > 0:
                flare_intensities.append(intensity)
                cme_speeds.append(speed)

        if flare_intensities and cme_speeds:
            ax3.scatter(flare_intensities, cme_speeds, c='purple', s=100, alpha=0.7, edgecolors='white')
            ax3.set_xlabel('Flare Intensity')
            ax3.set_ylabel('CME Speed (km/s)')
            ax3.set_title('Flare Intensity vs Associated CME Speed')
            ax3.grid(True, alpha=0.3)

            # Add trend line if enough points
            if len(flare_intensities) > 2:
                z = np.polyfit(flare_intensities, cme_speeds, 1)
                p = np.poly1d(z)
                x_line = np.linspace(min(flare_intensities), max(flare_intensities), 100)
                ax3.plot(x_line, p(x_line), 'r--', alpha=0.5, label='Trend')
                ax3.legend()
    else:
        ax3.text(0.5, 0.5, 'No linked FLR-CME pairs found', transform=ax3.transAxes,
                ha='center', va='center', fontsize=12)
        ax3.set_title('Flare Intensity vs Associated CME Speed')

    # 4. Time delay distribution for linked events
    ax4 = axes[1, 1]
    if linked_pairs:
        delays = []
        for flare, cme in linked_pairs:
            delay = (cme.start_time - flare.start_time).total_seconds() / 3600
            if delay > 0:
                delays.append(delay)

        if delays:
            ax4.hist(delays, bins=15, color='purple', alpha=0.8, edgecolor='white')
            ax4.axvline(x=np.median(delays), color='red', linestyle='--',
                       label=f'Median: {np.median(delays):.1f}h')
            ax4.set_xlabel('Time Delay (hours)')
            ax4.set_ylabel('Count')
            ax4.set_title('Flare-to-CME Time Delay')
            ax4.legend()
            ax4.grid(True, axis='y', alpha=0.3)
    else:
        ax4.text(0.5, 0.5, 'No linked FLR-CME pairs found', transform=ax4.transAxes,
                ha='center', va='center', fontsize=12)
        ax4.set_title('Flare-to-CME Time Delay')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"FLR-CME pairwise chart saved to: {save_path}")

    plt.show()
    return fig


def create_pairwise_cme_gst(cmes: list[SpaceEvent], storms: list[SpaceEvent], save_path: str = None):
    """Create pairwise comparison chart for CMEs and Geomagnetic Storms."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Coronal Mass Ejections vs Geomagnetic Storms', fontsize=14, fontweight='bold')

    cme_color = '#4ECDC4'
    gst_color = '#9B59B6'

    # Build lookup for linked events
    all_events = {e.event_id: e for e in cmes + storms}

    # Find linked CME-GST pairs
    linked_pairs = []
    for cme in cmes:
        for linked_id in cme.linked_events:
            if linked_id in all_events and all_events[linked_id].event_type == 'GST':
                gst = all_events[linked_id]
                linked_pairs.append((cme, gst))

    # 1. Dual timeline showing propagation
    ax1 = axes[0, 0]
    cme_times = [c.start_time for c in cmes]
    gst_times = [s.start_time for s in storms]

    ax1.scatter(cme_times, [1]*len(cme_times), c=cme_color, s=60, alpha=0.7, label='CMEs', edgecolors='white')
    ax1.scatter(gst_times, [0]*len(gst_times), c=gst_color, s=100, alpha=0.8, label='Geomagnetic Storms', edgecolors='white')

    # Draw propagation arrows
    for cme, gst in linked_pairs:
        ax1.annotate('', xy=(gst.start_time, 0), xytext=(cme.start_time, 1),
                    arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5, linewidth=2))

    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(['Earth Impact\n(GST)', 'Solar Corona\n(CME)'])
    ax1.set_xlabel('Date')
    ax1.set_title(f'CME-to-Earth Propagation ({len(linked_pairs)} linked events)')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.tick_params(axis='x', rotation=45)
    ax1.legend(loc='upper right')
    ax1.grid(True, axis='x', alpha=0.3)

    # 2. Travel time distribution
    ax2 = axes[0, 1]
    if linked_pairs:
        travel_times = []
        for cme, gst in linked_pairs:
            hours = (gst.start_time - cme.start_time).total_seconds() / 3600
            if hours > 0:
                travel_times.append(hours)

        if travel_times:
            ax2.hist(travel_times, bins=15, color='purple', alpha=0.8, edgecolor='white')
            avg_time = np.mean(travel_times)
            ax2.axvline(x=avg_time, color='red', linestyle='--',
                       label=f'Mean: {avg_time:.1f}h ({avg_time/24:.1f} days)')
            ax2.set_xlabel('Travel Time (hours)')
            ax2.set_ylabel('Count')
            ax2.set_title('CME-to-Earth Travel Time')
            ax2.legend()
            ax2.grid(True, axis='y', alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'No linked CME-GST pairs found', transform=ax2.transAxes,
                ha='center', va='center', fontsize=12)
        ax2.set_title('CME-to-Earth Travel Time')

    # 3. CME speed vs Storm Kp index
    ax3 = axes[1, 0]
    if linked_pairs:
        speeds = []
        kp_values = []
        for cme, gst in linked_pairs:
            speed = parse_cme_speed(cme.intensity)
            kp = parse_kp_index(gst.intensity)
            if speed > 0 and kp > 0:
                speeds.append(speed)
                kp_values.append(kp)

        if speeds and kp_values:
            ax3.scatter(speeds, kp_values, c='purple', s=100, alpha=0.7, edgecolors='white')
            ax3.set_xlabel('CME Speed (km/s)')
            ax3.set_ylabel('Storm Kp Index')
            ax3.set_title('CME Speed vs Resulting Storm Intensity')
            ax3.grid(True, alpha=0.3)

            # Add reference lines
            ax3.axhline(y=5, color='yellow', linestyle='--', alpha=0.5, label='G1 threshold')
            ax3.axhline(y=7, color='red', linestyle='--', alpha=0.5, label='G3 threshold')
            ax3.legend(loc='lower right')
    else:
        ax3.text(0.5, 0.5, 'No linked CME-GST pairs found', transform=ax3.transAxes,
                ha='center', va='center', fontsize=12)
        ax3.set_title('CME Speed vs Resulting Storm Intensity')

    # 4. CME speed vs travel time
    ax4 = axes[1, 1]
    if linked_pairs:
        speeds = []
        travel_times = []
        for cme, gst in linked_pairs:
            speed = parse_cme_speed(cme.intensity)
            hours = (gst.start_time - cme.start_time).total_seconds() / 3600
            if speed > 0 and hours > 0:
                speeds.append(speed)
                travel_times.append(hours)

        if speeds and travel_times:
            ax4.scatter(speeds, travel_times, c='purple', s=100, alpha=0.7, edgecolors='white')
            ax4.set_xlabel('CME Speed (km/s)')
            ax4.set_ylabel('Travel Time (hours)')
            ax4.set_title('CME Speed vs Travel Time to Earth')
            ax4.grid(True, alpha=0.3)

            # Faster CMEs should arrive sooner - add trend if enough points
            if len(speeds) > 2:
                z = np.polyfit(speeds, travel_times, 1)
                p = np.poly1d(z)
                x_line = np.linspace(min(speeds), max(speeds), 100)
                ax4.plot(x_line, p(x_line), 'r--', alpha=0.5, label='Trend')
                ax4.legend()
    else:
        ax4.text(0.5, 0.5, 'No linked CME-GST pairs found', transform=ax4.transAxes,
                ha='center', va='center', fontsize=12)
        ax4.set_title('CME Speed vs Travel Time to Earth')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"CME-GST pairwise chart saved to: {save_path}")

    plt.show()
    return fig


def create_pairwise_flr_gst(flares: list[SpaceEvent], storms: list[SpaceEvent],
                            cmes: list[SpaceEvent], save_path: str = None):
    """Create pairwise comparison chart for Solar Flares and Geomagnetic Storms."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Solar Flares vs Geomagnetic Storms (Full Sun-to-Earth)', fontsize=14, fontweight='bold')

    flr_color = '#FF6B6B'
    gst_color = '#9B59B6'

    # Build event chains: FLR -> CME -> GST
    all_events = {e.event_id: e for e in flares + cmes + storms}

    # Find full chain events
    full_chains = []  # (flare, cme, storm)
    for flare in flares:
        for cme_id in flare.linked_events:
            if cme_id in all_events and all_events[cme_id].event_type == 'CME':
                cme = all_events[cme_id]
                for gst_id in cme.linked_events:
                    if gst_id in all_events and all_events[gst_id].event_type == 'GST':
                        gst = all_events[gst_id]
                        full_chains.append((flare, cme, gst))

    # 1. Full propagation timeline
    ax1 = axes[0, 0]
    flr_times = [f.start_time for f in flares]
    gst_times = [s.start_time for s in storms]

    ax1.scatter(flr_times, [1]*len(flr_times), c=flr_color, s=60, alpha=0.7,
               label='Solar Flares', edgecolors='white')
    ax1.scatter(gst_times, [0]*len(gst_times), c=gst_color, s=100, alpha=0.8,
               label='Geomagnetic Storms', edgecolors='white')

    # Draw full chain connections
    for flare, cme, gst in full_chains:
        total_time = (gst.start_time - flare.start_time).total_seconds() / 3600
        ax1.annotate('', xy=(gst.start_time, 0), xytext=(flare.start_time, 1),
                    arrowprops=dict(arrowstyle='->', color='orange', alpha=0.6, linewidth=2))

    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(['Earth Impact', 'Sun Surface'])
    ax1.set_xlabel('Date')
    ax1.set_title(f'Sun-to-Earth Event Chain ({len(full_chains)} complete chains)')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.tick_params(axis='x', rotation=45)
    ax1.legend(loc='upper right')
    ax1.grid(True, axis='x', alpha=0.3)

    # 2. Total propagation time
    ax2 = axes[0, 1]
    if full_chains:
        total_times = []
        for flare, cme, gst in full_chains:
            hours = (gst.start_time - flare.start_time).total_seconds() / 3600
            if hours > 0:
                total_times.append(hours)

        if total_times:
            ax2.hist(total_times, bins=15, color='orange', alpha=0.8, edgecolor='white')
            avg = np.mean(total_times)
            ax2.axvline(x=avg, color='red', linestyle='--',
                       label=f'Mean: {avg:.1f}h ({avg/24:.1f} days)')
            ax2.set_xlabel('Total Time (hours)')
            ax2.set_ylabel('Count')
            ax2.set_title('Flare-to-Earth Total Propagation Time')
            ax2.legend()
            ax2.grid(True, axis='y', alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'No complete FLR→CME→GST\nchains found', transform=ax2.transAxes,
                ha='center', va='center', fontsize=12)
        ax2.set_title('Flare-to-Earth Total Propagation Time')

    # 3. Flare intensity vs storm Kp
    ax3 = axes[1, 0]
    if full_chains:
        flare_vals = []
        kp_vals = []
        for flare, cme, gst in full_chains:
            _, intensity = parse_flare_class(flare.intensity)
            kp = parse_kp_index(gst.intensity)
            if intensity > 0 and kp > 0:
                flare_vals.append(intensity)
                kp_vals.append(kp)

        if flare_vals and kp_vals:
            ax3.scatter(flare_vals, kp_vals, c='orange', s=100, alpha=0.7, edgecolors='white')
            ax3.set_xlabel('Flare Intensity')
            ax3.set_ylabel('Storm Kp Index')
            ax3.set_title('Initial Flare vs Final Storm Intensity')
            ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, 'No complete chains found', transform=ax3.transAxes,
                ha='center', va='center', fontsize=12)
        ax3.set_title('Initial Flare vs Final Storm Intensity')

    # 4. Event correlation heatmap by day
    ax4 = axes[1, 1]
    flr_dates = Counter([t.date() for t in flr_times])
    gst_dates = Counter([t.date() for t in gst_times])

    all_dates = sorted(set(flr_dates.keys()) | set(gst_dates.keys()))

    if all_dates:
        # Create simple overlay bar chart
        x = np.arange(len(all_dates))
        width = 0.35

        ax4.bar(x - width/2, [flr_dates.get(d, 0) for d in all_dates], width,
               label='Solar Flares', color=flr_color, alpha=0.8)
        ax4.bar(x + width/2, [gst_dates.get(d, 0) * 5 for d in all_dates], width,  # Scale GST for visibility
               label='Geomagnetic Storms (×5)', color=gst_color, alpha=0.8)

        ax4.set_xlabel('Date')
        ax4.set_ylabel('Count')
        ax4.set_title('Daily Solar Activity vs Earth Impact')
        ax4.set_xticks(x[::3])
        ax4.set_xticklabels([d.strftime('%m-%d') for d in all_dates][::3], rotation=45)
        ax4.legend()
        ax4.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"FLR-GST pairwise chart saved to: {save_path}")

    plt.show()
    return fig


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

        # Create visualizations
        if flares or cmes or storms:
            print("\nGenerating charts...")

            # Main timeline
            print("\n1. Combined Timeline Chart")
            title = f"Space Weather Events: {start_str} to {end_str}"
            create_timeline_chart(
                flares, cmes, storms,
                title=title,
                save_path="space_weather_timeline.png"
            )

            # Individual charts
            if flares:
                print("\n2. Solar Flare Analysis")
                create_flare_chart(flares, save_path="chart_flares.png")

            if cmes:
                print("\n3. CME Analysis")
                create_cme_chart(cmes, save_path="chart_cme.png")

            if storms:
                print("\n4. Geomagnetic Storm Analysis")
                create_gst_chart(storms, save_path="chart_gst.png")

            # Pairwise charts
            if flares and cmes:
                print("\n5. Flares vs CMEs Comparison")
                create_pairwise_flr_cme(flares, cmes, save_path="chart_flr_vs_cme.png")

            if cmes and storms:
                print("\n6. CMEs vs Geomagnetic Storms Comparison")
                create_pairwise_cme_gst(cmes, storms, save_path="chart_cme_vs_gst.png")

            if flares and storms:
                print("\n7. Flares vs Geomagnetic Storms (Full Chain)")
                create_pairwise_flr_gst(flares, storms, cmes, save_path="chart_flr_vs_gst.png")

            print("\n" + "="*60)
            print("All charts generated successfully!")
            print("="*60)
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
