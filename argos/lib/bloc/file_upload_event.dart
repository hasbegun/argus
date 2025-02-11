part of 'file_upload_bloc.dart';

abstract class FileUploadEvent extends Equatable {
  const FileUploadEvent();

  @override
  List<Object> get props => [];
}

class UploadFileEvent extends FileUploadEvent {
  final File file;
  final String? prompt;

  const UploadFileEvent({required this.file, this.prompt});

  @override
  List<Object> get props => [file, prompt ?? ""];
}