test_nums = [0, 1]

build_tree_dict = {}

for featured_category in test_nums:
    build_tree_dict["featured_category_data"] = {}
    build_tree_dict["featured_category_data"][str(featured_category)] = {'hello': 'world'}
    print(build_tree_dict["featured_category_data"][str(featured_category)])
    print(str(featured_category))
    print(str(1))
    # print(build_tree_dict["featured_category_data"][str(0)])