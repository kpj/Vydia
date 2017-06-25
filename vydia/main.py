"""
Main interface
"""

from .controller import Controller


def main():
    with Controller() as c:
        c.main()

if __name__ == '__main__':
    main()
