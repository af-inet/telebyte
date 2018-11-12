import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("targets", type=str)
    return parser.parse_args()


def format_row(x, y, spacing):
    cell = "%" + str(spacing) + "s"
    format_string = "  ".join([cell] * 4)
    result = format_string % tuple([x, y, '=', x*y])
    return result


def main():

    args = parse_args()

    targets = map(int, args.targets.split(","))

    start = 1
    end = max(targets)

    sign = 1 if end-start > 0 else -1

    numbers = range(start, end+sign, sign)

    values = [
        x
        for x in numbers
        # is this number divisible by all the targets?
        if sum([(target % x) for target in targets]) == 0
    ]

    for value in values:
        print(value)


main()
