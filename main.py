import streamlit as st
import csv
import pandas as pd
import altair as alt

# Set page title
st.title("East Glamorgan Chess Ratings App")

# Open and read the CSV files
with open('data.csv', 'r') as file:
    csv_reader = csv.DictReader(file)
    data = list(csv_reader)

# Load players data for rating lookup
players_df = pd.read_csv('players.csv')

# Get user input
search_name = st.text_input("Enter a player name to search:")

# Function to find player rating
def get_player_rating(player_name):
    """Look up player rating in players.csv"""
    if not player_name:
        return None
    # Strip whitespace from input
    player_name = player_name.strip()
    # Split the name into parts to match against firstname and lastname
    name_parts = player_name.lower().split()
    
    for idx, row in players_df.iterrows():
        firstname = str(row['firstname']).strip() if pd.notna(row['firstname']) else ''
        lastname = str(row['lastname']).strip() if pd.notna(row['lastname']) else ''
        full_name = f"{firstname} {lastname}".lower()
        if full_name == player_name.lower():
            rating = row['rating']
            if pd.notna(rating):
                return int(rating)
    return None

# Function to calculate ELO rating change
def calculate_elo_change(player_rating, opponent_rating, result, k_factor=None):
    """
    Calculate the rating change for a player based on ELO formula.

    K-factor tiers (used when `k_factor` is None):
      - rating < 1800: K = 30
      - 1800 <= rating <= 2200: K = 20
      - rating > 2200: K = 10

    Args:
        player_rating: Player's current rating
        opponent_rating: Opponent's current rating
        result: Match result (1 for win, 0.5 for draw, 0 for loss)
        k_factor: Optional override for K-factor. If None, tiers above are used.

    Returns:
        Rating change (can be positive or negative) or None if inputs missing.
    """
    if player_rating is None or opponent_rating is None:
        return None

    # Determine K-factor if not provided
    if k_factor is None:
        try:
            pr = float(player_rating)
        except (TypeError, ValueError):
            pr = None

        if pr is None:
            k = 32
        elif pr < 1800:
            k = 30
        elif pr <= 2200:
            k = 20
        else:
            k = 10
    else:
        k = k_factor

    # Calculate expected score
    expected_score = 1 / (1 + 10 ** ((opponent_rating - player_rating) / 400))

    # Calculate rating change
    rating_change = k * (result - expected_score)

    return round(rating_change)

# Search for the name in Player 1 or Player 2 columns
if search_name:
    # Display player rating at the top
    rating = get_player_rating(search_name)
    if rating:
        st.metric(label=f"Rating for {search_name}", value=rating)
    
    results = []
    # Get the searched player's rating for ELO calculation
    search_player_rating = get_player_rating(search_name)
    # Track live rating as matches are processed
    live_rating = search_player_rating
    
    search_name_lower = search_name.strip().lower()
    
    for record in data:
        player1 = record.get('Player 1', '').strip().lower()
        player2 = record.get('Player 2', '').strip().lower()
        
        if player1 == search_name_lower:
            # If found in Player 1, show Player 2 (opponent)
            result_value = record.get('Result', '')
            result_text = ''
            actual_score = None
            
            # Convert result to numeric value for ELO calculation
            try:
                actual_score = float(result_value)
                if actual_score == 1.0:
                    result_text = 'Win'
                elif actual_score == 0.5:
                    result_text = 'Draw'
                elif actual_score == 0.0:
                    result_text = 'Loss'
            except (ValueError, TypeError):
                actual_score = None
            
            opponent_name = record.get('Player 2', '').strip()
            opponent_rating = get_player_rating(opponent_name)
            rating_source = 'players.csv'
            # Fallback to rating from data.csv if not found in players.csv
            if opponent_rating is None:
                opponent_rating_str = record.get('Rating', '')
                if opponent_rating_str:
                    try:
                        opponent_rating = int(opponent_rating_str)
                        rating_source = 'data.csv'
                    except ValueError:
                        opponent_rating = None
            
            # Calculate ELO rating change only if opponent rating is available
            rating_change = None
            display_live_rating = None
            if opponent_rating is not None:
                rating_change = calculate_elo_change(live_rating, opponent_rating, actual_score)
                # Update live rating with the rating change (only if player has a rating)
                if live_rating is not None and rating_change is not None:
                    live_rating = live_rating + rating_change
                display_live_rating = live_rating
            
            results.append({'Date': record.get('Date', ''), 'Opponent': opponent_name, 'Rating': opponent_rating, 'Result': result_text, '_rating_source': rating_source, 'Rating Change': rating_change, 'Live Rating': display_live_rating})
        elif player2 == search_name_lower:
            # If found in Player 2, show Player 1 (opponent)
            result_value = record.get('Result', '')
            result_text = ''
            actual_score = None
            
            # Convert result to numeric value for ELO calculation, then invert for Player 2
            try:
                result_numeric = float(result_value)
                # Invert the score since this player was Player 2
                if result_numeric == 1.0:
                    actual_score = 0.0  # Player 2 lost
                    result_text = 'Loss'
                elif result_numeric == 0.5:
                    actual_score = 0.5  # Draw
                    result_text = 'Draw'
                elif result_numeric == 0.0:
                    actual_score = 1.0  # Player 2 won
                    result_text = 'Win'
            except (ValueError, TypeError):
                actual_score = None
            
            opponent_name = record.get('Player 1', '').strip()
            opponent_rating = get_player_rating(opponent_name)
            rating_source = 'players.csv'
            # Fallback to rating from data.csv if not found in players.csv
            if opponent_rating is None:
                opponent_rating_str = record.get('Rating', '')
                if opponent_rating_str:
                    try:
                        opponent_rating = int(opponent_rating_str)
                        rating_source = 'data.csv'
                    except ValueError:
                        opponent_rating = None
            
            # Calculate ELO rating change only if opponent rating is available
            rating_change = None
            display_live_rating = None
            if opponent_rating is not None:
                rating_change = calculate_elo_change(live_rating, opponent_rating, actual_score)
                # Update live rating with the rating change (only if player has a rating)
                if live_rating is not None and rating_change is not None:
                    live_rating = live_rating + rating_change
                display_live_rating = live_rating
            
            results.append({'Date': record.get('Date', ''), 'Opponent': opponent_name, 'Rating': opponent_rating, 'Result': result_text, '_rating_source': rating_source, 'Rating Change': rating_change, 'Live Rating': display_live_rating})

    # Display results
    if results:
        st.success(f"Found {len(results)} match(es) for '{search_name}':")
        df = pd.DataFrame(results)
        
        # Create a dataframe for the chart with game numbers
        chart_df = df[['Live Rating']].copy()
        chart_df['Game Number'] = range(1, len(chart_df) + 1)
        chart_df = chart_df[chart_df['Live Rating'].notna()]  # Filter out games with no rating
        
        # Display line chart with rescaled y-axis
        if not chart_df.empty:
            # Get min and max for better y-axis scaling with padding
            min_rating = chart_df['Live Rating'].min()
            max_rating = chart_df['Live Rating'].max()
            padding = (max_rating - min_rating) * 0.1  # 10% padding
            
            chart = alt.Chart(chart_df).mark_line(point=True).encode(
                x=alt.X('Game Number:Q', title='Game #'),
                y=alt.Y('Live Rating:Q', title='Rating', 
                        scale=alt.Scale(domain=[min_rating - padding, max_rating + padding]))
            ).properties(height=400, width=700)
            
            st.altair_chart(chart, use_container_width=True)
        
        # Display table below the chart
        st.subheader("Match Details")
        data_csv_rows = df[df['_rating_source'] == 'data.csv'].index.tolist()
        
        # Drop the _rating_source column for display
        df_display = df.drop('_rating_source', axis=1)
        
        # Apply styling to the Rating column (red if from data.csv) and Rating Change column (green for gains, red for losses)
        styled_df = df_display.style.map(
            lambda v: 'color: red;' if not pd.isna(v) else '',
            subset=pd.IndexSlice[data_csv_rows, 'Rating']
        )
        
        # Color the Rating Change column: green for positive, red for negative
        styled_df = styled_df.map(
            lambda v: 'color: green;' if (v is not None and v > 0) else ('color: red;' if (v is not None and v < 0) else ''),
            subset=['Rating Change']
        )
        
        # Format Rating, Rating Change, and Live Rating columns to display with no decimal places
        styled_df = styled_df.format({
            'Rating': '{:.0f}',
            'Rating Change': '{:.0f}',
            'Live Rating': '{:.0f}'
        })
        
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.warning(f"No records found for '{search_name}'")
