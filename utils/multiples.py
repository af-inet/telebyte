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

    values = [
        [x] + [x * y for y in xrange(start, end+1)]
        for x in xrange(start, end+1)
    ]

    spacing = len(str(end * end))

    header = [""] + range(start, end+1)

    print(format_row(header, spacing))

    for row in values:
        print(format_row(row, spacing))


main()
