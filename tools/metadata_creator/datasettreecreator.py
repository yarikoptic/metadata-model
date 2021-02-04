import json
import os
import time
from typing import Generator, Optional, Tuple
from uuid import UUID

from dataladmetadatamodel import JSONObject
from dataladmetadatamodel.connector import Connector
from dataladmetadatamodel.datasettree import DatasetTree
from dataladmetadatamodel.metadata import ExtractorConfiguration, Metadata
from dataladmetadatamodel.metadatarootrecord import MetadataRootRecord

from tools.metadata_creator.execute import checked_execute
from tools.metadata_creator.filetreecreator import create_file_tree


DATALAD_DATASET_HIDDEN_DIR_NAME = ".datalad"


def has_datalad_dir(path: str) -> bool:
    return any(
        filter(
            lambda e: e.is_dir(follow_symlinks=False) and e.name == DATALAD_DATASET_HIDDEN_DIR_NAME,
            os.scandir(path)))


def is_dataset_dir(entry: os.DirEntry) -> bool:
    return entry.is_dir(follow_symlinks=False) and has_datalad_dir(entry.path)


def should_follow(entry: os.DirEntry, ignore_dot_dirs) -> bool:
    return (
        entry.is_dir(follow_symlinks=False)
        and not entry.name.startswith(".") or ignore_dot_dirs is False)


def read_datasets(path: str, ignore_dot_dirs: bool = True) -> Generator[Tuple[str, os.DirEntry], None, None]:
    """ Return all datasets und path """

    if has_datalad_dir(path):
        path_entry = tuple(filter(lambda e: path.endswith(e.name), os.scandir(path + "/..")))[0]
        yield ".", path_entry

    entries = list(os.scandir(path))
    while entries:
        entry = entries.pop()
        if is_dataset_dir(entry):
            yield entry.path[len(path) + 1:], entry
        if should_follow(entry, ignore_dot_dirs):
            entries.extend(list(os.scandir(entry.path)))


def get_extractor_run(path: str, entry: os.DirEntry):
    stat = entry.stat(follow_symlinks=False)
    return {
        "path": path,
        "size": stat.st_size,
        "atime": stat.st_atime,
        "ctime": stat.st_ctime,
        "mtime": stat.st_mtime,
    }


def get_dataset_info(path) -> JSONObject:
    stdout_content, _ = checked_execute(["datalad", "-C", path, "-f", "json_pp", "wtf"])
    return json.loads(stdout_content)


def add_metadata_root_record(mapper_family,
                             realm,
                             dataset_tree: DatasetTree,
                             path,
                             entry: os.DirEntry):

    # Too slow: dataset_info = get_dataset_info(entry.path)
    dataset_info = dict(dataset=dict(id="00000000-95ed-11ea-af77-7cdd908c7490"))

    file_tree = create_file_tree(mapper_family, realm, entry.path)

    metadata = Metadata(mapper_family, realm)
    metadata.add_extractor_run(
            time.time(),
            "dataset-test-extractor",
            "datasetcreator.py",
            "support@datalad.org",
            ExtractorConfiguration("1.2.3", {"parameter_a": "value_a"}),
            {"info": "fake metadata for dataset-test-extractor", "path": path}
        )


    mrr = MetadataRootRecord(
        mapper_family,
        realm,
        UUID(dataset_info["dataset"]["id"]),
        "1234567891123456789212345678931234567894",
         Connector.from_object(metadata),
         Connector.from_object(file_tree)
    )
    dataset_tree.add_dataset(path, mrr)


def update_dataset_tree(mapper_family: str,
                        realm: str,
                        dataset_tree: DatasetTree,
                        root_dir: str,
                        parameter: Optional[dict] = None):

    for path, entry in read_datasets(root_dir):
        add_metadata_root_record(mapper_family, realm, dataset_tree, path, entry)


def create_dataset_tree(mapper_family: str,
                        realm: str,
                        root_dir: str,
                        parameter: Optional[dict] = None) -> DatasetTree:

    dataset_tree = DatasetTree(mapper_family, realm)
    update_dataset_tree(mapper_family, realm, dataset_tree, root_dir, parameter)
    return dataset_tree