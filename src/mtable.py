import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)
    return parser.parse_args()


def format_row(values, spacing):
    cell = "%" + str(spacing) + "s"
    format_string = "  ".join([cell] * len(values))
    result = format_string % tuple(values)
    return result


def main():

    args = parse_args()
    start = args.start
    end = args.end

    sign = 1 if end-start > 0 else -1

    numbers = range(start, end+sign, sign)

    values = [
        [x] + [x * y for y in numbers]
        for x in numbers
    ]

    spacing = len(str(max(numbers) ** 2))

    # first cell in the header will be blank
    header = [""] + numbers

    print(format_row(header, spacing))

    for row in values:
        print(format_row(row, spacing))


main()
