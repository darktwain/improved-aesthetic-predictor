import argparse
import os
import random
import pickle


def write_data_to_pickle_file(data, file_name):
    with open(file_name, 'wb') as fp:
        pickle.dump(data, fp)

    print('Wrote {} entries to {}'.format(len(data), file_name))


def get_data_from_pickle(file_name):
    if not os.path.isfile(file_name):
        return {}

    with open(file_name, 'rb') as fp:
        try:
            data = pickle.load(fp)
            print('Loaded {} entries from {}'.format(len(data), file_name))
            return data
        except EOFError:
            print('Loaded 0 entries from {}'.format(file_name))
            return {}


def main():
    parser = argparse.ArgumentParser(description='Calculates aesthetic scores.')
    parser.add_argument('--dir', dest='dir', required=True)
    args = parser.parse_args()
    images_folder = args.dir
    scores_pickle_file = os.path.join(images_folder, 'aesthetic-score-pickle')
    print('images_folder {}'.format(images_folder))
    print('scores_pickle_file {}'.format(scores_pickle_file))
    scores = get_data_from_pickle(scores_pickle_file)

    from simple_inference import simple_inference as si

    for image_file in os.listdir(images_folder):
        image_path = os.path.join(images_folder, image_file)

        if image_file in scores:
            continue
        try:
            score = si.get_aesthetic_score(image_path)
        except OSError:
            continue

        if score is None:
            continue

        scores[image_file] = score

        if random.randint(0, 100) == 1:
            write_data_to_pickle_file(scores, scores_pickle_file)

    write_data_to_pickle_file(scores, scores_pickle_file)


if __name__ == "__main__":
    main()
