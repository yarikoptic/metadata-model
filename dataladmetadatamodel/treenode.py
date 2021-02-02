from typing import Any, List, Optional, Tuple


class TreeNode:
    def __init__(self,
                 value: Optional[Any] = None):
        self.child_nodes = dict()
        self.value = value

    def is_leaf_node(self):
        return len(self.child_nodes) == 0

    def add_node(self, name: str, new_node: "TreeNode"):
        self.add_nodes([(name, new_node)])

    def add_nodes(self, new_nodes: List[Tuple[str, "TreeNode"]]):
        new_names = set(map(lambda new_entry: new_entry[0], new_nodes))
        duplicated_names = set(self.child_nodes.keys()) & new_names
        if duplicated_names:
            raise ValueError("Name(s) already exist(s): " + ", ".join(duplicated_names))
        self.child_nodes = {
            **self.child_nodes,
            **dict(new_nodes)
        }

    def add_node_hierarchy(self,
                           path: str,
                           new_node: "TreeNode",
                           allow_leaf_node_conversion: bool = False):
        self._add_node_hierarchy(
            path.split("/"),
            new_node,
            allow_leaf_node_conversion
        )

    def _add_node_hierarchy(self,
                            path_elements: List[str],
                            new_node: "TreeNode",
                            allow_leaf_node_conversion: bool):
        if len(path_elements) == 1:
            self.add_node(path_elements[0], new_node)
        else:
            sub_node = self.child_nodes.get(path_elements[0], None)
            if not sub_node:
                sub_node = TreeNode()
                self.add_node(path_elements[0], sub_node)
            else:
                if not allow_leaf_node_conversion and sub_node.is_leaf_node():
                    raise ValueError(f"Cannot replace leaf node with name {path_elements[0]} with a directory node")
            sub_node._add_node_hierarchy(path_elements[1:], new_node, allow_leaf_node_conversion)

    def add_node_hierarchies(self, new_node_hierarchies: List[Tuple[str, "TreeNode"]]):
        for path_node_tuple in new_node_hierarchies:
            self.add_node_hierarchy(*path_node_tuple)

    def get_sub_node(self, name: str):
        return self.child_nodes[name]

    def get_node_at_path(self, path: str = "") -> Optional["TreeNode"]:
        """ Simple linear path-search """
        path_elements = path.split("/") if path != "" else []
        current_node = self
        for element in path_elements:
            try:
                current_node = current_node.get_sub_node(element)
            except KeyError:
                return None
        return current_node

    def get_paths(self):
        return tuple(self.child_nodes.keys())

    def get_paths_recursive(self, show_intermediate: Optional[bool] = False) -> List[Tuple[str, "TreeNode"]]:
        if show_intermediate or self.is_leaf_node():
            result = [("", self)]
        else:
            result = []
        for child_name, child_node in self.child_nodes.items():
            child_node_infos = child_node.get_paths_recursive(show_intermediate)
            result += [
                (
                    child_name + ("/" + child_node_info[0] if child_node_info[0] else ""),
                    child_node_info[1]
                )
                for child_node_info in child_node_infos
            ]
        return result