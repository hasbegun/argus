part of 'file_upload_bloc.dart';

abstract class FileUploadState extends Equatable {
  const FileUploadState();

  @override
  List<Object> get props => [];
}

class FileUploadInitial extends FileUploadState {}

class FileUploading extends FileUploadState {}

class FileUploadSuccess extends FileUploadState {
  final File file;
  final Map<String, dynamic> response;

  const FileUploadSuccess({required this.file, required this.response});

  @override
  List<Object> get props => [file, response];
}

class FileUploadFailure extends FileUploadState {
  final String error;

  const FileUploadFailure({required this.error});

  @override
  List<Object> get props => [error];
}