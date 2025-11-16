import matplotlib.pyplot as plt
import numpy as np

# --- NEW DATASET (Reflecting your provided image) ---
# This dataset includes artists, their approximate birth/form years, and genres.
# I've used the exact data points and their associated genres from your image.
data = [
    {"artist": "Ti Frère", "year": 1900, "genre": "Sega Typik"},
    {"artist": "Serge Lebrasse", "year": 1934, "genre": "Sega"},
    {"artist": "Michel Legris", "year": 1936, "genre": "Sega"},
    {"artist": "Fanfan", "year": 1930, "genre": "Sega"}, # Adjusted slightly for spacing on graph
    {"artist": "Roger Augustin", "year": 1938, "genre": "Sega"},
    {"artist": "Cyril Labonne", "year": 1940, "genre": "Sega"},
    {"artist": "George Joe", "year": 1945, "genre": "Sega"},
    {"artist": "Claudio Veeraragoo", "year": 1947, "genre": "Sega"},
    {"artist": "Coqloce", "year": 1950, "genre": "Sega"}, # Adjusted slightly for spacing
    {"artist": "Roger Clency", "year": 1952, "genre": "Sega"},
    {"artist": "Jean-Claude Gaspard", "year": 1955, "genre": "Sega"},
    {"artist": "Ti L'Afrique", "year": 1957, "genre": "Sega"},
    {"artist": "Menwar", "year": 1965, "genre": "Sega"},
    {"artist": "Ras Natty Baby", "year": 1968, "genre": "Seggae"}, # Approx from image
    {"artist": "Kaya", "year": 1970, "genre": "Seggae"}, # Approx from image
    {"artist": "Berger Agathe", "year": 1972, "genre": "Sega"}, # Approx from image
    {"artist": "Alain Ramanisum", "year": 1975, "genre": "Sega/Reggae"}, # Approx from image
    {"artist": "Blakkayo", "year": 1978, "genre": "Sega/Reggae"}, # Approx from image
    {"artist": "Linzy Bacbotte", "year": 1980, "genre": "Soul Sega"}, # Approx from image
    {"artist": "Groupe Latanier", "year": 1982, "genre": "Sega/Reggae/Soul"}, # Approx from image
    {"artist": "Lin", "year": 1985, "genre": "Seggae"}, # Approx from image
    {"artist": "Anne Ga", "year": 1990, "genre": "Sagaï"}, # Approx from image
    {"artist": "Cassiya", "year": 1992, "genre": "Sega"},
    {"artist": "OSB", "year": 1995, "genre": "Santé engagé"}, # Approx from image
]

# Sort data by year to ensure correct chronological plotting
data.sort(key=lambda x: x['year'])

artists = [d['artist'] for d in data]
years = [d['year'] for d in data]
genres = [d['genre'] for d in data]

# --- Custom Color Mapping for Genres (based on your image's legend) ---
genre_colors = {
    "Sega Typik": "#b74143", # Darker red/maroon
    "Sega": "#dd3b3b",      # Red
    "Soul Sega": "#8B4513", # Saddle brown
    "Sagaï": "#4CAF50",     # Green
    "Seggae": "#00BFFF",    # Deep Sky Blue
    "Seggae/Ragga": "#CD853F", # Peru
    "Sega/Reggae/Soul": "#800080", # Purple
    "Sega/Reggae": "#4682B4", # SteelBlue
    "Sega/Pop/Soul": "#A9A9A9", # DarkGray
    "Santé engagé": "#FFD700", # Gold
    # Add any other genres you might have in your dataset with their desired colors
}

# Assign colors to each artist based on their genre
artist_colors = [genre_colors.get(g, '#808080') for g in genres] # Default to grey if genre not found

# --- Matplotlib Plotting Setup ---
fig, ax = plt.subplots(figsize=(12, 10))

# Set background color to match the image
fig.patch.set_facecolor('#f9f7f0')
ax.set_facecolor('#f9f7f0')

# Create a custom y-coordinate for each artist to ensure vertical spacing
# We will just plot them sequentially along the y-axis
y_coords = np.arange(len(artists)) * 1.0  # Adjust multiplier for more or less vertical space

# Plot each artist
for i, (artist, year, genre, color) in enumerate(zip(artists, years, genres, artist_colors)):
    # Plot the circle marker
    ax.plot(year, y_coords[i], 'o', color=color, markersize=8, zorder=3,
            markeredgecolor='white', markeredgewidth=0.8) # White edge as in image

    # Add artist name text
    ax.text(year + 1.5, y_coords[i], artist,
            ha='left', va='center', fontsize=9, color='#36454F') # Dark grey text

# --- Formatting the Graph ---
ax.set_title('Mauritian Sega Artists Timeline',
             fontsize=20, fontweight='bold', color='#36454F', pad=25) # Darker title

ax.set_xlabel('Birth/Form Yr', fontsize=14, color='#36454F', labelpad=15) # X-axis label as in image

# Set X-axis ticks to match the image (1900, 1920, 1940, 1960, 1980)
ax.set_xticks(np.arange(1900, 2001, 20))
ax.set_xticklabels(np.arange(1900, 2001, 20), fontsize=10, color='#36454F')

# Set y-axis to be invisible
ax.yaxis.set_visible(False)

# Remove all spines
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['bottom'].set_color('#cccccc') # Light grey bottom spine

# Add vertical grid lines
ax.grid(axis='x', linestyle='-', color='#cccccc', alpha=0.7, zorder=0)

# Adjust plot limits for better spacing
ax.set_xlim(1895, 2000) # Extend slightly before 1900 and after last year
ax.set_ylim(-1, len(artists)) # Adjust y-limits to fit all points comfortably

# --- Custom Legend ---
# Create a list of legend handles and labels
legend_elements = []
for genre, color in genre_colors.items():
    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', label=genre,
                                      markerfacecolor=color, markersize=10, markeredgecolor='white', markeredgewidth=0.8))

# Place the legend on the right side of the plot
ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1),
          title="", frameon=False, fontsize=9, labelcolor='#36454F')


plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout to make space for the legend on the right
plt.show()