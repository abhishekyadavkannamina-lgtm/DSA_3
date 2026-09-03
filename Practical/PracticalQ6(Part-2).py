# Bitmask Dynamic Programming
# for subset optimization

values = [10, 20, 30, 40]

max_items = 2

n = len(values)

best_value = 0

best_subset = []


# Generate every possible subset
for mask in range(1 << n):

    total = 0

    selected = []

    # Check every item
    for i in range(n):

        # Check whether ith bit is set
        if mask & (1 << i):

            total += values[i]

            selected.append(values[i])

    # Check constraint
    if len(selected) <= max_items:

        # Update best solution
        if total > best_value:

            best_value = total

            best_subset = selected


# Display result
print("Maximum number of items =", max_items)
print("Best selected items =", best_subset)
print("Maximum value =", best_value)