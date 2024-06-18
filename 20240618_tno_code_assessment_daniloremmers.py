import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


##########
## Read and analyse CSV data
###

def read_csv_files(position, numtags):
    # Prepare library for potential expansion of number of tags
    data_frames = {}
    # Tag name generation: A, B, ..., Z, AA, AB, etc.
    for person in range(numtags):
        if person <= 25:
            letter1 = chr(person + 65)
            tagfilename = f'Tag{letter1}.csv'
            tag_var = f'tag_{letter1.lower()}'
            data_frames[tag_var] = tagfilename
        else:
            iteration = person // 26
            letters12 = f'{chr(iteration + 64)}{chr((person % 26) + 65)}'
            tagfilename = f'Tag{letters12}.csv'
            tag_var = f'tag_{letters12.lower()}'
            data_frames[tag_var] = tagfilename
    # Turn csv data into a more easily readable dataframe
    # Includes manual reading of tag_a and tag_b; Can later be expanded to have the program process larger libraries
    tag_a_df = pd.read_csv(data_frames['tag_a'])
    tag_b_df = pd.read_csv(data_frames['tag_b'])
    position_df = pd.read_csv(position)
    return tag_a_df, tag_b_df, position_df

def check_tag_connections(tag_a_df, tag_b_df):
    # Verification of which tagIDs are read by both Tag A and Tag B.
    # This also forms a starting point for identification of missing or false connections if the number of tags increases.
    unique_tags_a = tag_a_df['ContactID'].unique()
    unique_tags_b = tag_b_df['ContactID'].unique()
    print(f'Contact IDs from Tag A: {unique_tags_a}\n'
          f'Contact IDs from Tag B: {unique_tags_b}')


def verify_distances(tag_a_df, tag_b_df):
    merged_tags = pd.merge(tag_a_df, tag_b_df, on='Time [s]', suffixes=('_A', '_B'))
    merged_tags['distance_match'] = np.isclose(merged_tags['Distance [m]_A'], merged_tags['Distance [m]_B'])
    mismatched_distances = merged_tags[~merged_tags['distance_match']]
    if not mismatched_distances.empty:
        print("Mismatched distances between Tag A and Tag B files")
        print(mismatched_distances[['Time [s]', 'Distance [m]_A', 'Distance [m]_B']])
    else:
        print("All distances between Tag A and Tag B match.")

    # Count uninterrupted periods within 1.5m
    within_1_5m = (merged_tags['Distance [m]_A'] <= 1.5) & (merged_tags['Distance [m]_B'] <= 1.5)
    uninterrupted_periods = 0
    in_contact = False
    for i in range(len(within_1_5m)):
        # verify if not already in contact, otherwise we count it as a new contact
        if within_1_5m.iloc[i]:
            if not in_contact:
                uninterrupted_periods += 1
                in_contact = True
        else:
            in_contact = False
    print(f"Uninterrupted sessions between tag A and B within 1.5 meters: {uninterrupted_periods}")


def correct_tag_ids(position_df):
    unique_tags = position_df['TagID'].unique()
    # To be expanded if number of tags increases
    if len(unique_tags) != len(position_df) // len(unique_tags):
        print("Measurement Error: Duplicate TagID detected at single timepoint")
        # Change the TagID of the wrongly labelled tag (Currently specifically looks at the case of A and B)
        tag_ids = position_df['TagID'].unique()
        next_available_letter = chr(ord(max(tag_ids)) + 1)
        position_df.loc[position_df.index % 2 == 1, 'TagID'] = next_available_letter
    return position_df


##########
## Visualisation
###

def plot_positions(position_df, contact_within_1_5m):
    # Collect position data per tag
    position_a = position_df[position_df['TagID'] == 'A']
    position_b = position_df[position_df['TagID'] == 'B']

    plt.figure(figsize=(10, 10))
    # Tracks of each tag over time; can be removed if only the contact points should be visualised.
    plt.plot(position_a['x [m]'], position_a['y[m]'], label='Tag A', alpha=0.7)
    plt.plot(position_b['x [m]'], position_b['y[m]'], label='Tag B', alpha=0.7)
    # Plot of each timepoint in which Tag A and Tag B are within 1,5m of each other
    plt.scatter(contact_within_1_5m['x [m]'], contact_within_1_5m['y[m]'], color='red',
                label='Contact Points between tag A and B (within 1.5m)', s=10)
    plt.xlim(0, 10)
    plt.ylim(0, 10)
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    plt.title('Tag tracks + Contact points within 1.5 m (dt = 0.1s)')
    plt.legend()
    plt.grid(True)
    plt.show()


##########
## Main function to execute separate analyses
###
def tag_analysis(tag_a, tag_b, position, numtags):
    tag_a_df, tag_b_df, position_df = read_csv_files(position, numtags)

    # Check which Tag IDs were read by tag A
    check_tag_connections(tag_a_df, tag_b_df)

    # Correct Tag IDs if necessary
    position_df_corrected = correct_tag_ids(position_df)

    # Verify distances between Tag A and Tag B
    verify_distances(tag_a_df, tag_b_df)

    # Determine the duration of contact within 1.5 meters between A and B
    contact_within_1_5m_a = tag_a_df[tag_a_df['Distance [m]'] <= 1.5]
    contact_within_1_5m_b = tag_b_df[tag_b_df['Distance [m]'] <= 1.5]

    # Merge contact_within_1_5m_[tagID] with position_df to get position data for plotting the contact moments
    # Including both a and b, as they might have more tags to connect to in the future
    contact_within_1_5m_a_pos = pd.merge(contact_within_1_5m_a, position_df[position_df['TagID'] == 'A'], on='Time [s]')
    contact_within_1_5m_b_pos = pd.merge(contact_within_1_5m_b, position_df[position_df['TagID'] == 'B'], on='Time [s]')

    total_contact_duration = min(len(contact_within_1_5m_a), len(contact_within_1_5m_b)) * 0.1  # Each time step is 0.1 seconds

    print("Total contact duration within 1.5 meters: ", total_contact_duration)

    # Plot positions
    plot_positions(position_df_corrected, contact_within_1_5m_a_pos)


##########
## Definitions & parameters
###

# Edit file names & path if necessary
tag_a_path = 'TagA.csv'
tag_b_path = 'TagB.csv'
position_path = 'position.csv'

numtags = 2  # number of tags in the room - edit parameter if necessary

# Initiate analysis & visualisation of position and tag files
tag_analysis(tag_a_path, tag_b_path, position_path, numtags)
